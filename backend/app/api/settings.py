from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db_session
from app.database.models import Setting, User
from app.security.dependencies import get_current_user
from app.config import settings as app_settings


router = APIRouter()


class SettingCreate(BaseModel):
    key: str
    value: str
    description: Optional[str] = None
    is_secret: bool = False


class SettingUpdate(BaseModel):
    value: str
    description: Optional[str] = None


@router.get("")
async def list_settings(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Setting).where(Setting.user_id == current_user.id)
    )
    user_settings = result.scalars().all()
    
    system_settings = {
        "agent_name": app_settings.AGENT_NAME,
        "model_provider": app_settings.MODEL_PROVIDER,
        "model_name": app_settings.MODEL_NAME,
        "enable_browser": app_settings.ENABLE_BROWSER,
        "enable_github": app_settings.ENABLE_GITHUB,
        "enable_remote_access": app_settings.ENABLE_REMOTE_ACCESS,
        "enable_scheduler": app_settings.ENABLE_SCHEDULER,
        "enable_notifications": app_settings.ENABLE_NOTIFICATIONS,
    }
    
    return {
        "system": system_settings,
        "user": [
            {
                "key": s.key,
                "value": s.value if not s.is_secret else "***",
                "description": s.description,
                "is_secret": s.is_secret,
            }
            for s in user_settings
        ],
    }


@router.post("", status_code=201)
async def create_setting(
    request: SettingCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    existing = await db.execute(
        select(Setting).where(Setting.user_id == current_user.id, Setting.key == request.key)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Setting already exists")
    
    setting = Setting(
        user_id=current_user.id,
        key=request.key,
        value=request.value,
        description=request.description,
        is_secret=request.is_secret,
    )
    db.add(setting)
    await db.flush()
    
    return {"key": setting.key, "value": setting.value if not setting.is_secret else "***"}


@router.get("/{key}")
async def get_setting(
    key: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Setting).where(Setting.user_id == current_user.id, Setting.key == key)
    )
    setting = result.scalar_one_or_none()
    
    if not setting:
        if key in ["agent_name", "model_provider", "model_name"]:
            return {"key": key, "value": getattr(app_settings, key.upper()), "is_system": True}
        raise HTTPException(status_code=404, detail="Setting not found")
    
    return {
        "key": setting.key,
        "value": setting.value if not setting.is_secret else "***",
        "description": setting.description,
        "is_secret": setting.is_secret,
    }


@router.put("/{key}")
async def update_setting(
    key: str,
    request: SettingUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Setting).where(Setting.user_id == current_user.id, Setting.key == key)
    )
    setting = result.scalar_one_or_none()
    
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    setting.value = request.value
    if request.description is not None:
        setting.description = request.description
    
    await db.flush()
    
    return {"key": setting.key, "value": setting.value if not setting.is_secret else "***"}


@router.delete("/{key}")
async def delete_setting(
    key: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Setting).where(Setting.user_id == current_user.id, Setting.key == key)
    )
    setting = result.scalar_one_or_none()
    
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    await db.delete(setting)
    await db.commit()
    
    return {"message": "Setting deleted"}