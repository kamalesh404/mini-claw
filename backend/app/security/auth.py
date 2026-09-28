from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from passlib.context import CryptContext
from jose import jwt, JWTError

from app.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(user_id: str, device_id: Optional[str] = None, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": user_id,
        "type": "access",
        "jti": str(uuid4()),
        "exp": expire,
    }
    if device_id:
        to_encode["device_id"] = device_id
    
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str, device_id: Optional[str] = None) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "sub": user_id,
        "type": "refresh",
        "jti": str(uuid4()),
        "exp": expire,
    }
    if device_id:
        to_encode["device_id"] = device_id
    
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    payload = decode_token(token)
    if not payload:
        return None
    if payload.get("type") != token_type:
        return None
    return payload.get("sub")


def generate_device_token() -> str:
    return str(uuid4())


def hash_token(token: str) -> str:
    return get_password_hash(token)