from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db_session
from app.database.models import Memory
from app.security.dependencies import get_current_user, get_user_permissions
from app.tools.registry import tool_registry
from app.security.permissions import check_tool_permission
from app.main import memory_manager


router = APIRouter()


class MemoryCreate(BaseModel):
    category: str
    key: str
    value: str
    metadata: Optional[Dict[str, Any]] = None
    is_sensitive: bool = False


class MemoryUpdate(BaseModel):
    value: str
    metadata: Optional[Dict[str, Any]] = None


@router.post("", status_code=201)
async def create_memory(
    request: MemoryCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    memory = await memory_manager.add_memory(
        db, current_user.id, request.category, request.key,
        request.value, request.metadata, request.is_sensitive
    )
    return {"id": memory.id, "category": memory.category, "key": memory.key}


@router.get("")
async def list_memories(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    category: Optional[str] = None,
    limit: int = 100,
):
    memories = await memory_manager.list_memories(db, current_user.id, category, limit)
    return [
        {
            "id": m.id,
            "category": m.category,
            "key": m.key,
            "value": m.value,
            "metadata": m.metadata,
            "is_sensitive": m.is_sensitive,
            "created_at": m.created_at.isoformat(),
            "updated_at": m.updated_at.isoformat(),
        }
        for m in memories
    ]


@router.get("/search")
async def search_memories(
    query: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    category: Optional[str] = None,
    limit: int = 10,
):
    memories = await memory_manager.search_memories(db, current_user.id, query, category, limit)
    return [
        {
            "id": m.id,
            "category": m.category,
            "key": m.key,
            "value": m.value,
            "metadata": m.metadata,
            "is_sensitive": m.is_sensitive,
            "created_at": m.created_at.isoformat(),
            "updated_at": m.updated_at.isoformat(),
        }
        for m in memories
    ]


@router.get("/{category}/{key}")
async def get_memory(
    category: str,
    key: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    memory = await memory_manager.get_memory(db, current_user.id, category, key)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {
        "id": memory.id,
        "category": memory.category,
        "key": memory.key,
        "value": memory.value,
        "metadata": memory.metadata,
        "is_sensitive": memory.is_sensitive,
        "created_at": memory.created_at.isoformat(),
        "updated_at": memory.updated_at.isoformat(),
    }


@router.put("/{category}/{key}")
async def update_memory(
    category: str,
    key: str,
    request: MemoryUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    memory = await memory_manager.update_memory(
        db, current_user.id, category, key, request.value, request.metadata
    )
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"id": memory.id, "category": memory.category, "key": memory.key}


@router.delete("/{category}/{key}")
async def delete_memory(
    category: str,
    key: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    success = await memory_manager.delete_memory(db, current_user.id, category, key)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"message": "Memory deleted"}