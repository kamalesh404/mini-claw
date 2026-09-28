from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.tools.registry import BaseTool, ToolInputSchema, ToolOutput, PermissionLevel
from app.security.permissions import Permission
from app.scheduler.manager import SchedulerManager


class SchedulerToolBase(BaseTool):
    def __init__(self, scheduler: SchedulerManager):
        super().__init__()
        self.scheduler = scheduler


class CreateTaskInput(ToolInputSchema):
    name: str
    trigger_type: str = Field(pattern="^(cron|interval|date|event)$")
    trigger_config: Dict[str, Any]
    action_type: str
    action_config: Dict[str, Any]
    conditions: Optional[List[Dict[str, Any]]] = Field(default=None)


class CreateTaskTool(SchedulerToolBase):
    name = "create_task"
    description = "Create a scheduled task"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.SCHEDULER_WRITE]
    input_schema = CreateTaskInput
    
    async def execute(self, input_data: CreateTaskInput) -> ToolOutput:
        try:
            task_id = await self.scheduler.create_task(
                name=input_data.name,
                trigger_type=input_data.trigger_type,
                trigger_config=input_data.trigger_config,
                action_type=input_data.action_type,
                action_config=input_data.action_config,
                conditions=input_data.conditions,
            )
            return ToolOutput(success=True, data={"task_id": task_id})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class UpdateTaskInput(ToolInputSchema):
    task_id: str
    name: Optional[str] = Field(default=None)
    trigger_config: Optional[Dict[str, Any]] = Field(default=None)
    action_config: Optional[Dict[str, Any]] = Field(default=None)
    conditions: Optional[List[Dict[str, Any]]] = Field(default=None)
    is_enabled: Optional[bool] = Field(default=None)


class UpdateTaskTool(SchedulerToolBase):
    name = "update_task"
    description = "Update a scheduled task"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.SCHEDULER_WRITE]
    input_schema = UpdateTaskInput
    
    async def execute(self, input_data: UpdateTaskInput) -> ToolOutput:
        try:
            await self.scheduler.update_task(
                input_data.task_id,
                name=input_data.name,
                trigger_config=input_data.trigger_config,
                action_config=input_data.action_config,
                conditions=input_data.conditions,
                is_enabled=input_data.is_enabled,
            )
            return ToolOutput(success=True, data={"task_id": input_data.task_id})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class DeleteTaskInput(ToolInputSchema):
    task_id: str


class DeleteTaskTool(SchedulerToolBase):
    name = "delete_task"
    description = "Delete a scheduled task"
    permission_level = PermissionLevel.DANGEROUS
    required_permissions = [Permission.SCHEDULER_ADMIN]
    input_schema = DeleteTaskInput
    
    async def execute(self, input_data: DeleteTaskInput) -> ToolOutput:
        try:
            await self.scheduler.delete_task(input_data.task_id)
            return ToolOutput(success=True, data={"task_id": input_data.task_id})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class ListTasksInput(ToolInputSchema):
    enabled_only: bool = Field(default=False)


class ListTasksTool(SchedulerToolBase):
    name = "list_tasks"
    description = "List scheduled tasks"
    permission_level = PermissionLevel.READ_ONLY
    required_permissions = [Permission.SCHEDULER_READ]
    input_schema = ListTasksInput
    
    async def execute(self, input_data: ListTasksInput) -> ToolOutput:
        try:
            tasks = await self.scheduler.list_tasks(input_data.enabled_only)
            return ToolOutput(success=True, data={"tasks": tasks})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class RunTaskNowInput(ToolInputSchema):
    task_id: str


class RunTaskNowTool(SchedulerToolBase):
    name = "run_task_now"
    description = "Run a task immediately"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.SCHEDULER_WRITE]
    input_schema = RunTaskNowInput
    
    async def execute(self, input_data: RunTaskNowInput) -> ToolOutput:
        try:
            result = await self.scheduler.run_task_now(input_data.task_id)
            return ToolOutput(success=True, data=result)
        except Exception as e:
            return ToolOutput(success=False, error=str(e))