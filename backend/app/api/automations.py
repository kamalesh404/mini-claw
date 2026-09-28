from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.security.dependencies import get_current_user, get_user_permissions
from app.tools.registry import tool_registry
from app.security.permissions import check_tool_permission
from app.main import scheduler


router = APIRouter()


class CreateAutomationRequest(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: str
    trigger_config: Dict[str, Any]
    action_type: str
    action_config: Dict[str, Any]
    conditions: Optional[List[Dict[str, Any]]] = None


class UpdateAutomationRequest(BaseModel):
    name: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    action_config: Optional[Dict[str, Any]] = None
    conditions: Optional[List[Dict[str, Any]]] = None
    is_enabled: Optional[bool] = None


@router.post("", status_code=201)
async def create_automation(
    request: CreateAutomationRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("create_task", {**request.model_dump(), "user_id": current_user.id}, user_permissions)


@router.get("")
async def list_automations(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    enabled_only: bool = False,
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("list_tasks", {"enabled_only": enabled_only}, user_permissions)


@router.get("/{automation_id}")
async def get_automation(
    automation_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    automations = await _execute_tool("list_tasks", {"enabled_only": False}, get_user_permissions(current_user))
    for a in automations.get("tasks", []):
        if a["id"] == automation_id:
            return a
    raise HTTPException(status_code=404, detail="Automation not found")


@router.patch("/{automation_id}")
async def update_automation(
    automation_id: str,
    request: UpdateAutomationRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("update_task", {"task_id": automation_id, **request.model_dump(exclude_unset=True)}, user_permissions)


@router.delete("/{automation_id}")
async def delete_automation(
    automation_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("delete_task", {"task_id": automation_id}, user_permissions)


@router.post("/{automation_id}/run")
async def run_automation_now(
    automation_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("run_task_now", {"task_id": automation_id}, user_permissions)


async def _execute_tool(tool_name: str, args: dict, permissions):
    tool = tool_registry.get(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    if not check_tool_permission(permissions, tool_name):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    output = await tool_registry.execute_tool(tool_name, args, permissions)
    if not output.success:
        raise HTTPException(status_code=500, detail=output.error)
    return output.data