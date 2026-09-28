from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database.session import get_db_session
from app.database.models import Notification, Device
from app.security.dependencies import get_current_user


router = APIRouter()


class DevicePushSubscription(BaseModel):
    endpoint: str
    keys: Dict[str, str]


class RegisterDeviceRequest(BaseModel):
    name: str
    device_type: str
    platform: str
    push_subscription: Optional[DevicePushSubscription] = None


@router.get("")
async def list_notifications(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    unread_only: bool = False,
    limit: int = 50,
):
    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.is_read == False)
    query = query.order_by(desc(Notification.created_at)).limit(limit)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return [
        {
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "body": n.body,
            "data": n.data,
            "is_read": n.is_read,
            "sent_at": n.sent_at.isoformat() if n.sent_at else None,
            "read_at": n.read_at.isoformat() if n.read_at else None,
            "created_at": n.created_at.isoformat(),
        }
        for n in notifications
    ]


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Notification marked as read"}


@router.post("/read-all")
async def mark_all_read(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )
    notifications = result.scalars().all()
    
    for n in notifications:
        n.is_read = True
        n.read_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": f"Marked {len(notifications)} notifications as read"}


@router.post("/devices/register")
async def register_device(
    request: RegisterDeviceRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    from app.security.auth import generate_device_token
    
    device_token = generate_device_token()
    
    device = Device(
        user_id=current_user.id,
        name=request.name,
        device_type=request.device_type,
        platform=request.platform,
        device_token=device_token,
        push_subscription=request.push_subscription.model_dump() if request.push_subscription else None,
    )
    db.add(device)
    await db.flush()
    
    return {"device_id": device.id, "device_token": device_token}


@router.get("/devices")
async def list_devices(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Device).where(Device.user_id == current_user.id, Device.is_active == True)
    )
    devices = result.scalars().all()
    
    return [
        {
            "id": d.id,
            "name": d.name,
            "device_type": d.device_type,
            "platform": d.platform,
            "has_push_subscription": d.push_subscription is not None,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
        }
        for d in devices
    ]


@router.delete("/devices/{device_id}")
async def unregister_device(
    device_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.user_id == current_user.id)
    )
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device.is_active = False
    await db.commit()
    
    return {"message": "Device unregistered"}


from datetime import datetime