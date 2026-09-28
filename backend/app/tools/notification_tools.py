from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.tools.registry import BaseTool, ToolInputSchema, ToolOutput, PermissionLevel
from app.security.permissions import Permission
from app.services.notifications import NotificationService


class NotificationToolBase(BaseTool):
    def __init__(self, notification_service: NotificationService):
        super().__init__()
        self.notifications = notification_service


class SendMobileNotificationInput(ToolInputSchema):
    user_id: str
    title: str
    body: str
    data: Optional[Dict[str, Any]] = Field(default=None)
    priority: str = Field(default="normal", pattern="^(low|normal|high)$")


class SendMobileNotificationTool(NotificationToolBase):
    name = "send_mobile_notification"
    description = "Send a push notification to mobile device"
    permission_level = PermissionLevel.SAFE_LOCAL
    required_permissions = [Permission.NOTIFICATION_SEND]
    input_schema = SendMobileNotificationInput
    
    async def execute(self, input_data: SendMobileNotificationInput) -> ToolOutput:
        try:
            await self.notifications.send_push(
                input_data.user_id,
                input_data.title,
                input_data.body,
                input_data.data,
                input_data.priority,
            )
            return ToolOutput(success=True, data={"sent": True})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class SendEmailInput(ToolInputSchema):
    to: List[str]
    subject: str
    body: str
    html: Optional[str] = Field(default=None)


class SendEmailTool(NotificationToolBase):
    name = "send_email"
    description = "Send an email"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.NOTIFICATION_SEND]
    input_schema = SendEmailInput
    
    async def execute(self, input_data: SendEmailInput) -> ToolOutput:
        try:
            await self.notifications.send_email(
                input_data.to,
                input_data.subject,
                input_data.body,
                input_data.html,
            )
            return ToolOutput(success=True, data={"sent": True})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class SendWebNotificationInput(ToolInputSchema):
    user_id: str
    title: str
    body: str
    icon: Optional[str] = Field(default=None)
    actions: Optional[List[Dict[str, str]]] = Field(default=None)


class SendWebNotificationTool(NotificationToolBase):
    name = "send_web_notification"
    description = "Send a web push notification"
    permission_level = PermissionLevel.SAFE_LOCAL
    required_permissions = [Permission.NOTIFICATION_SEND]
    input_schema = SendWebNotificationInput
    
    async def execute(self, input_data: SendWebNotificationInput) -> ToolOutput:
        try:
            await self.notifications.send_web_push(
                input_data.user_id,
                input_data.title,
                input_data.body,
                input_data.icon,
                input_data.actions,
            )
            return ToolOutput(success=True, data={"sent": True})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))