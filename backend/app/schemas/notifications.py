from pydantic import BaseModel
from datetime import datetime
import uuid


class NotificationListItem(BaseModel):
    id: uuid.UUID
    title: str
    message: str
    category: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    total: int
    items: list[NotificationListItem]


class SendEmailResponse(BaseModel):
    status: str
    provider: str
    to_email: str
    subject: str
    email_log_id: uuid.UUID
