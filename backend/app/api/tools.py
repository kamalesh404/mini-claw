from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.security.dependencies import get_current_user, get_user_permissions
from app.tools.registry import tool_registry
from app.security.permissions import check_tool_permission


router = APIRouter()


class ToolExecuteRequest(BaseModel):
    tool: str
    args: Dict[str, Any]


class ToolExecuteResponse(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


@router.get("")
async def list_tools():
    return {"tools": tool_registry.list_tools()}


@router.get("/{tool_name}")
async def get_tool(tool_name: str):
    tool = tool_registry.get(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool.get_schema()


@router.post("/execute", response_model=ToolExecuteResponse)
async def execute_tool(
    request: ToolExecuteRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    
    if not check_tool_permission(user_permissions, request.tool):
        raise HTTPException(status_code=403, detail=f"Permission denied for tool: {request.tool}")
    
    output = await tool_registry.execute_tool(request.tool, request.args, user_permissions)
    
    return ToolExecuteResponse(
        success=output.success,
        data=output.data,
        error=output.error,
        metadata=output.metadata,
    )