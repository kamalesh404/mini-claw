from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from app.database.session import get_db_session
from app.database.models import User, Device, Session as SessionModel
from app.security.auth import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
    verify_token, generate_device_token, hash_token,
)
from app.security.dependencies import get_current_user, get_current_user_optional


router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str
    device_name: str = "Unknown Device"
    device_type: str = "web"
    platform: str = "unknown"


class RefreshRequest(BaseModel):
    refresh_token: str


class DeviceRegisterRequest(BaseModel):
    name: str
    device_type: str
    platform: str
    push_subscription: dict = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
):
    existing = await db.execute(
        select(User).where(
            (User.username == request.username) | (User.email == request.email)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    user = User(
        username=request.username,
        email=request.email,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
    )
    db.add(user)
    await db.flush()
    
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    session = SessionModel(
        user_id=user.id,
        access_token=hash_token(access_token),
        refresh_token=hash_token(refresh_token),
        expires_at=datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        refresh_expires_at=datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    
    device_token = generate_device_token()
    
    device_result = await db.execute(
        select(Device).where(Device.device_token == device_token)
    )
    device = device_result.scalar_one_or_none()
    
    if not device:
        device = Device(
            user_id=user.id,
            name=request.device_name,
            device_type=request.device_type,
            platform=request.platform,
            device_token=device_token,
        )
        db.add(device)
        await db.flush()
    
    access_token = create_access_token(user.id, device.id)
    refresh_token = create_refresh_token(user.id, device.id)
    
    session = SessionModel(
        user_id=user.id,
        device_id=device.id,
        access_token=hash_token(access_token),
        refresh_token=hash_token(refresh_token),
        expires_at=datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        refresh_expires_at=datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session)
    
    user.last_login = datetime.utcnow()
    device.last_seen = datetime.utcnow()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db_session),
):
    user_id = verify_token(request.refresh_token, "refresh")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    result = await db.execute(
        select(SessionModel).where(
            SessionModel.refresh_token == hash_token(request.refresh_token),
            SessionModel.is_revoked == False,
        )
    )
    session = result.scalar_one_or_none()
    
    if not session or session.refresh_expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired")
    
    new_access = create_access_token(user_id, session.device_id)
    new_refresh = create_refresh_token(user_id, session.device_id)
    
    session.access_token = hash_token(new_access)
    session.refresh_token = hash_token(new_refresh)
    session.expires_at = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    session.refresh_expires_at = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(SessionModel).where(SessionModel.user_id == current_user.id)
    )
    sessions = result.scalars().all()
    
    for session in sessions:
        session.is_revoked = True
    
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_admin": current_user.is_admin,
    }


@router.post("/devices", status_code=201)
async def register_device(
    request: DeviceRegisterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    device_token = generate_device_token()
    
    device = Device(
        user_id=current_user.id,
        name=request.name,
        device_type=request.device_type,
        platform=request.platform,
        device_token=device_token,
        push_subscription=request.push_subscription,
    )
    db.add(device)
    await db.flush()
    
    return {"device_id": device.id, "device_token": device_token}


@router.get("/devices")
async def list_devices(
    current_user: User = Depends(get_current_user),
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
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
        }
        for d in devices
    ]


from datetime import datetime
from app.config import settings