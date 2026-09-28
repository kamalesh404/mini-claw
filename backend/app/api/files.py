from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.security.dependencies import get_current_user, get_user_permissions
from app.tools.registry import tool_registry
from app.security.permissions import check_tool_permission


router = APIRouter()


class ListFilesRequest(BaseModel):
    path: str = "."
    recursive: bool = False
    include_hidden: bool = False
    pattern: Optional[str] = None


class SearchFilesRequest(BaseModel):
    pattern: str
    path: str = "."
    file_type: Optional[str] = None
    max_results: int = 100


class ReadFileRequest(BaseModel):
    path: str
    encoding: str = "utf-8"
    max_size: int = 1024*1024


class CreateFileRequest(BaseModel):
    path: str
    content: str = ""
    encoding: str = "utf-8"
    overwrite: bool = False


class EditFileRequest(BaseModel):
    path: str
    old_text: str
    new_text: str
    encoding: str = "utf-8"


class RenameFileRequest(BaseModel):
    old_path: str
    new_path: str


class MoveFileRequest(BaseModel):
    source: str
    destination: str
    overwrite: bool = False


class CopyFileRequest(BaseModel):
    source: str
    destination: str
    overwrite: bool = False


class DeleteFileRequest(BaseModel):
    path: str
    recursive: bool = False
    confirm: bool = False


@router.post("/list")
async def list_files(
    request: ListFilesRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("list_files", request.model_dump(), user_permissions)


@router.post("/search")
async def search_files(
    request: SearchFilesRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("search_files", request.model_dump(), user_permissions)


@router.post("/read")
async def read_file(
    request: ReadFileRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("read_file", request.model_dump(), user_permissions)


@router.post("/create")
async def create_file(
    request: CreateFileRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("create_file", request.model_dump(), user_permissions)


@router.post("/edit")
async def edit_file(
    request: EditFileRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("edit_file", request.model_dump(), user_permissions)


@router.post("/rename")
async def rename_file(
    request: RenameFileRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("rename_file", request.model_dump(), user_permissions)


@router.post("/move")
async def move_file(
    request: MoveFileRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("move_file", request.model_dump(), user_permissions)


@router.post("/copy")
async def copy_file(
    request: CopyFileRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("copy_file", request.model_dump(), user_permissions)


@router.post("/delete")
async def delete_file(
    request: DeleteFileRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("delete_file", request.model_dump(), user_permissions)


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