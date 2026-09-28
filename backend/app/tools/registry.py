from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4

from app.database.models import PermissionLevel
from app.security.permissions import Permission


class ToolInputSchema(BaseModel):
    pass


class ToolOutput(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolCallRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    tool_name: str
    input_args: Dict[str, Any]
    output: Optional[ToolOutput] = None
    permission_level: PermissionLevel
    approval_required: bool
    approval_id: Optional[str] = None
    execution_time_ms: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    permission_level: PermissionLevel = PermissionLevel.READ_ONLY
    required_permissions: List[Permission] = []
    input_schema: Type[ToolInputSchema] = ToolInputSchema
    
    def __init__(self):
        if not self.name:
            raise ValueError("Tool must have a name")
        if not self.description:
            raise ValueError("Tool must have a description")
    
    @abstractmethod
    async def execute(self, input_data: ToolInputSchema) -> ToolOutput:
        pass
    
    def validate(self, input_data: Dict[str, Any]) -> ToolInputSchema:
        return self.input_schema(**input_data)
    
    def audit(self, input_data: Dict[str, Any], output: ToolOutput) -> Dict[str, Any]:
        return {
            "tool": self.name,
            "input": input_data,
            "output": output.model_dump() if output else None,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "permission_level": self.permission_level.value,
            "required_permissions": [p.value for p in self.required_permissions],
            "input_schema": self.input_schema.model_json_schema(),
        }


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool
    
    def unregister(self, tool_name: str) -> None:
        if tool_name not in self._tools:
            raise KeyError(f"Tool '{tool_name}' not found")
        del self._tools[tool_name]
    
    def get(self, tool_name: str) -> Optional[BaseTool]:
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [tool.get_schema() for tool in self._tools.values()]
    
    def get_tools_by_permission(self, permission_level: PermissionLevel) -> List[BaseTool]:
        return [
            tool for tool in self._tools.values()
            if tool.permission_level == permission_level
        ]
    
    async def execute_tool(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        user_permissions: "PermissionSet",
    ) -> ToolOutput:
        tool = self.get(tool_name)
        if not tool:
            return ToolOutput(success=False, error=f"Tool '{tool_name}' not found")
        
        if not user_permissions.has_all(*tool.required_permissions):
            return ToolOutput(
                success=False,
                error=f"Insufficient permissions for tool '{tool_name}'"
            )
        
        try:
            validated_input = tool.validate(input_data)
            output = await tool.execute(validated_input)
            return output
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


tool_registry = ToolRegistry()