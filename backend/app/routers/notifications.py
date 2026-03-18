from __future__ import annotations

import uuid
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.notification import Notification, EmailLog
from app.schemas.documents import SendEmailRequest
from app.schemas.notifications import (
    NotificationListItem,
    NotificationListResponse,
    SendEmailResponse,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(True),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.is_read.is_(False))

    query = query.order_by(Notification.created_at.desc()).limit(limit)
    result = await db.execute(query)
    rows = result.scalars().all()

    return NotificationListResponse(
        total=len(rows),
        items=[NotificationListItem.model_validate(row) for row in rows],
    )


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    try:
        notif_uuid = uuid.UUID(notification_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid notification ID")

    result = await db.execute(
        select(Notification).where(
            Notification.id == notif_uuid,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    notification.updated_at = datetime.utcnow()
    await db.commit()

    return {"id": str(notification.id), "is_read": True}


@router.post("/send-email", response_model=SendEmailResponse)
async def send_email(
    body: SendEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    provider = "sendgrid"
    status = "queued"
    error_message = None
    provider_message_id = None

    if settings.NOTIFICATIONS_EMAIL_ENABLED and settings.SENDGRID_API_KEY:
        payload = {
            "personalizations": [{"to": [{"email": body.to_email}]}],
            "from": {"email": settings.SENDGRID_FROM_EMAIL},
            "subject": body.subject,
            "content": [{"type": "text/plain", "value": body.body}],
        }
        headers = {
            "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post("https://api.sendgrid.com/v3/mail/send", headers=headers, json=payload)

        if resp.status_code in {200, 202}:
            status = "sent"
            provider_message_id = resp.headers.get("X-Message-Id")
        else:
            status = "failed"
            error_message = resp.text[:1000]
    else:
        provider = "disabled"
        status = "skipped"

    log = EmailLog(
        tenant_id=current_user.tenant_id,
        to_email=body.to_email,
        from_email=settings.SENDGRID_FROM_EMAIL,
        subject=body.subject,
        template_name=body.category,
        status=status,
        provider=provider,
        provider_message_id=provider_message_id,
        error_message=error_message,
        event_type="manual_trigger",
        metadata_json={"requested_by": str(current_user.id)},
        sent_at=datetime.utcnow() if status == "sent" else None,
    )
    db.add(log)

    notification = Notification(
        user_id=current_user.id,
        title="Email dispatch",
        message=f"Email '{body.subject}' to {body.to_email} is {status}.",
        category="email",
        is_read=False,
        metadata_payload={"email_log_status": status},
    )
    db.add(notification)

    await db.commit()
    await db.refresh(log)

    if status == "failed":
        raise HTTPException(status_code=502, detail=f"SendGrid error: {error_message}")

    return SendEmailResponse(
        status=status,
        provider=provider,
        to_email=body.to_email,
        subject=body.subject,
        email_log_id=log.id,
    )
