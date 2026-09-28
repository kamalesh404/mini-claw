from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
import json

from app.models.providers import (
    LLMProvider, Message, ToolDefinition, LLMResponse, LLMStreamChunk,
    create_llm_provider,
)
from app.tools.registry import tool_registry, ToolOutput
from app.security.permissions import PermissionSet, check_tool_permission
from app.database.models import Task, TaskStep, ToolCall, Approval, PermissionLevel, TaskStatus, ApprovalStatus
from app.config import settings


@dataclass
class AgentContext:
    user_id: str
    conversation_id: Optional[str] = None
    task_id: Optional[str] = None
    permissions: PermissionSet = field(default_factory=PermissionSet)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentOrchestrator:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        tools = tool_registry.list_tools()
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool['name']}: {tool['description']}")
        
        return f"""You are MiniClaw, a personal AI automation agent running on the user's Windows PC.

You have access to the following tools:
{chr(10).join(tool_descriptions)}

Guidelines:
1. Always understand the user's request before acting
2. Break complex tasks into steps
3. Use tools through structured calls only
4. Ask for clarification when needed
5. Request approval for dangerous operations
6. Verify results before reporting success
7. Never execute arbitrary shell commands directly
8. Respect permission levels and user consent

When you need to use a tool, call it with the appropriate parameters.
Wait for the tool result before continuing.
"""
    
    def _get_tool_definitions(self) -> List[ToolDefinition]:
        tools = tool_registry.list_tools()
        return [
            ToolDefinition(
                name=tool["name"],
                description=tool["description"],
                parameters=tool["input_schema"],
            )
            for tool in tools
        ]
    
    async def chat(
        self,
        user_message: str,
        context: AgentContext,
        conversation_history: List[Message],
        stream: bool = False,
    ) -> AsyncGenerator[LLMStreamChunk, None] | LLMResponse:
        messages = [
            Message(role="system", content=self.system_prompt),
            *conversation_history,
            Message(role="user", content=user_message),
        ]
        
        tools = self._get_tool_definitions()
        
        if stream:
            return self._stream_chat(messages, tools, context)
        else:
            return await self._complete_chat(messages, tools, context)
    
    async def _complete_chat(
        self,
        messages: List[Message],
        tools: List[ToolDefinition],
        context: AgentContext,
    ) -> LLMResponse:
        response = await self.llm.complete(messages, tools)
        
        if response.tool_calls:
            for tool_call in response.tool_calls:
                await self._execute_tool_call(tool_call, context)
        
        return response
    
    async def _stream_chat(
        self,
        messages: List[Message],
        tools: List[ToolDefinition],
        context: AgentContext,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        full_content = ""
        tool_calls_buffer: Dict[str, Dict] = {}
        
        async for chunk in self.llm.stream(messages, tools):
            if chunk.content:
                full_content += chunk.content
            if chunk.tool_calls:
                for tc in chunk.tool_calls:
                    if tc["id"] not in tool_calls_buffer:
                        tool_calls_buffer[tc["id"]] = tc
                    else:
                        if tc.get("function", {}).get("arguments"):
                            tool_calls_buffer[tc["id"]]["function"]["arguments"] += tc["function"]["arguments"]
            
            yield chunk
        
        if tool_calls_buffer:
            for tool_call in tool_calls_buffer.values():
                await self._execute_tool_call(tool_call, context)
    
    async def _execute_tool_call(self, tool_call: Dict[str, Any], context: AgentContext) -> ToolOutput:
        function = tool_call.get("function", {})
        tool_name = function.get("name")
        arguments = function.get("arguments", {})
        
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}
        
        if not check_tool_permission(context.permissions, tool_name):
            return ToolOutput(
                success=False,
                error=f"Permission denied for tool: {tool_name}"
            )
        
        tool = tool_registry.get(tool_name)
        if not tool:
            return ToolOutput(success=False, error=f"Tool not found: {tool_name}")
        
        required_level = tool.permission_level
        
        if required_level >= PermissionLevel.DANGEROUS and context.task_id:
            return ToolOutput(
                success=False,
                error=f"Tool {tool_name} requires approval",
                metadata={"approval_required": True, "tool_name": tool_name, "arguments": arguments}
            )
        
        output = await tool_registry.execute_tool(tool_name, arguments, context.permissions)
        
        return output


class TaskExecutor:
    def __init__(self, orchestrator: AgentOrchestrator):
        self.orchestrator = orchestrator
    
    async def execute_task(
        self,
        task: Task,
        context: AgentContext,
        db_session,
    ) -> Task:
        task.status = TaskStatus.PLANNING
        task.started_at = datetime.utcnow()
        
        plan = await self._create_plan(task, context)
        task.plan = plan
        task.total_steps = len(plan)
        
        task.status = TaskStatus.RUNNING
        
        for i, step in enumerate(plan):
            task.current_step = i + 1
            task.progress = int((i / len(plan)) * 100)
            
            step_record = TaskStep(
                id=str(uuid4()),
                task_id=task.id,
                step_number=i + 1,
                tool_name=step["tool"],
                description=step["description"],
                input_args=step["args"],
            )
            db_session.add(step_record)
            await db_session.flush()
            
            tool_call = await self.orchestrator._execute_tool_call({
                "id": str(uuid4()),
                "type": "function",
                "function": {"name": step["tool"], "arguments": step["args"]}
            }, context)
            
            step_record.output_result = tool_call.data if tool_call.success else None
            step_record.error = tool_call.error
            step_record.status = "completed" if tool_call.success else "failed"
            step_record.started_at = datetime.utcnow()
            step_record.completed_at = datetime.utcnow()
            
            tool_call_record = ToolCall(
                id=str(uuid4()),
                task_id=task.id,
                step_id=step_record.id,
                tool_name=step["tool"],
                input_args=step["args"],
                output_result=tool_call.data if tool_call.success else None,
                error=tool_call.error,
                permission_level=tool_registry.get(step["tool"]).permission_level if tool_registry.get(step["tool"]) else PermissionLevel.READ_ONLY,
            )
            db_session.add(tool_call_record)
            
            if not tool_call.success:
                task.status = TaskStatus.FAILED
                task.error = tool_call.error
                task.completed_at = datetime.utcnow()
                return task
        
        task.status = TaskStatus.COMPLETED
        task.progress = 100
        task.completed_at = datetime.utcnow()
        task.result = "Task completed successfully"
        
        return task
    
    async def _create_plan(self, task: Task, context: AgentContext) -> List[Dict[str, Any]]:
        planning_prompt = f"""Create a step-by-step plan to accomplish this task:
Task: {task.title}
Description: {task.description or 'No description'}

Available tools: {json.dumps([t['name'] for t in tool_registry.list_tools()])}

Return a JSON array of steps, each with:
- tool: tool name
- description: what this step does
- args: arguments for the tool

Example:
[
  {{"tool": "list_files", "description": "List project files", "args": {{"path": "."}}}},
  {{"tool": "run_tests", "description": "Run tests", "args": {{"path": "."}}}}
]
"""
        
        messages = [
            Message(role="system", content=self.orchestrator.system_prompt),
            Message(role="user", content=planning_prompt),
        ]
        
        response = await self.orchestrator.llm.complete(messages)
        
        try:
            plan = json.loads(response.content or "[]")
            return plan
        except json.JSONDecodeError:
            return []