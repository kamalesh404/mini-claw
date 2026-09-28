from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db_session
from app.database.models import User, Session as SessionModel, Device
from app.security.auth import verify_token, decode_token
from app.security.permissions import PermissionSet, Permission, get_permissions_for_level
from app.config import settings


security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = verify_token(credentials.credentials, "access")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_user_optional(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Optional[User]:
    if not credentials:
        return None
    
    user_id = verify_token(credentials.credentials, "access")
    if not user_id:
        return None
    
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    return result.scalar_one_or_none()


async def get_current_device(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Optional[Device]:
    if not credentials:
        return None
    
    payload = decode_token(credentials.credentials)
    if not payload:
        return None
    
    device_id = payload.get("device_id")
    if not device_id:
        return None
    
    result = await db.execute(select(Device).where(Device.id == device_id, Device.is_active == True))
    return result.scalar_one_or_none()


def get_user_permissions(user: User) -> PermissionSet:
    if user.is_admin:
        return PermissionSet(permissions=set(Permission))
    
    # Default to DEVELOPER level for authenticated users
    # In the future, this could be configurable per user
    return PermissionSet(permissions=get_permissions_for_level(PermissionLevel.DEVELOPER))


async def require_permission(
    permission: Permission,
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    user_permissions = get_user_permissions(current_user)
    if not user_permissions.has(permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission.value}",
        )
    return current_user


def require_permissions(*permissions: Permission):
    async def permission_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        user_permissions = get_user_permissions(current_user)
        if not user_permissions.has_all(*permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissions denied: {[p.value for p in permissions]}",
            )
        return current_user
    return permission_checker