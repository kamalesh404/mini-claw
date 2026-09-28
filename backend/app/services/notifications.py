from typing import List, Optional, Dict, Any
import httpx
from pywebpush import webpush
from firebase_admin import messaging, credentials, initialize_app

from app.config import settings
from app.database.models import Device, Notification


class NotificationService:
    def __init__(self):
        self._firebase_initialized = False
        if settings.WEB_PUSH_VAPID_PRIVATE_KEY and settings.WEB_PUSH_VAPID_PUBLIC_KEY:
            self._vapid_private_key = settings.WEB_PUSH_VAPID_PRIVATE_KEY
            self._vapid_public_key = settings.WEB_PUSH_VAPID_PUBLIC_KEY
            self._vapid_claims = {"sub": settings.WEB_PUSH_VAPID_CLAIMS_SUB}
        else:
            self._vapid_private_key = None
            self._vapid_public_key = None
            self._vapid_claims = None
    
    def _init_firebase(self):
        if not self._firebase_initialized and settings.FIREBASE_CREDENTIALS_PATH:
            try:
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                initialize_app(cred)
                self._firebase_initialized = True
            except Exception:
                pass
    
    async def send_push(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
    ):
        from app.database.session import get_session
        
        async with get_session() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(Device).where(Device.user_id == user_id, Device.is_active == True)
            )
            devices = result.scalars().all()
            
            for device in devices:
                if device.push_subscription and self._vapid_private_key:
                    await self._send_web_push(device.push_subscription, title, body, data)
                
                if device.device_token and device.platform in ["android", "ios"]:
                    await self._send_fcm(device.device_token, title, body, data, priority)
    
    async def _send_web_push(
        self,
        subscription: Dict[str, Any],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
    ):
        try:
            webpush(
                subscription_info=subscription,
                data={
                    "title": title,
                    "body": body,
                    "data": data or {},
                },
                vapid_private_key=self._vapid_private_key,
                vapid_claims=self._vapid_claims,
            )
        except Exception:
            pass
    
    async def _send_fcm(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
    ):
        self._init_firebase()
        if not self._firebase_initialized:
            return
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data={k: str(v) for k, v in (data or {}).items()},
                android=messaging.AndroidConfig(
                    priority=priority if priority != "normal" else "normal",
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(alert=messaging.ApsAlert(title=title, body=body))
                    )
                ),
                token=token,
            )
            messaging.send(message)
        except Exception:
            pass
    
    async def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        html: Optional[str] = None,
    ):
        if not settings.SMTP_HOST:
            return
        
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = ", ".join(to)
            
            msg.attach(MIMEText(body, "plain"))
            if html:
                msg.attach(MIMEText(html, "html"))
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
        except Exception:
            pass
    
    async def send_web_push(
        self,
        user_id: str,
        title: str,
        body: str,
        icon: Optional[str] = None,
        actions: Optional[List[Dict[str, str]]] = None,
    ):
        await self.send_push(user_id, title, body, {"icon": icon, "actions": actions})
    
    async def create_notification(
        self,
        db,
        user_id: str,
        type: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        notification = Notification(
            id=str(uuid4()),
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            data=data or {},
        )
        db.add(notification)
        await db.flush()
        return notification


from uuid import uuid4