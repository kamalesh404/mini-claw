from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.security.dependencies import get_current_user, get_user_permissions
from app.tools.registry import tool_registry
from app.security.permissions import check_tool_permission


router = APIRouter()


@router.get("/status")
async def get_system_status(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    
    tools = [
        "get_system_info", "get_cpu_usage", "get_gpu_usage", 
        "get_ram_usage", "get_disk_usage", "get_network_info",
        "get_battery_status",
    ]
    
    results = {}
    for tool_name in tools:
        if check_tool_permission(user_permissions, tool_name):
            tool = tool_registry.get(tool_name)
            if tool:
                output = await tool_registry.execute_tool(tool_name, {}, user_permissions)
                results[tool_name] = output.data if output.success else {"error": output.error}
    
    return results


@router.get("/system")
async def get_system_info(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("get_system_info", {}, user_permissions)


@router.get("/cpu")
async def get_cpu_usage(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("get_cpu_usage", {}, user_permissions)


@router.get("/gpu")
async def get_gpu_usage(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("get_gpu_usage", {}, user_permissions)


@router.get("/ram")
async def get_ram_usage(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("get_ram_usage", {}, user_permissions)


@router.get("/disk")
async def get_disk_usage(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("get_disk_usage", {}, user_permissions)


@router.get("/network")
async def get_network_info(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("get_network_info", {}, user_permissions)


@router.get("/battery")
async def get_battery_status(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("get_battery_status", {}, user_permissions)


@router.get("/processes")
async def list_processes(
    limit: int = 50,
    sort_by: str = "cpu",
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("list_processes", {"limit": limit, "sort_by": sort_by}, user_permissions)


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