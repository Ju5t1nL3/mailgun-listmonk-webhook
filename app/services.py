import logging

import httpx
from fastapi import HTTPException

from app.schemas import (
    EventData,
    EventSeverity,
    EventType,
    ListmonkMeta,
    ListmonkPayload,
    ListmonkSeverity,
    WebhookErrorCode,
    WebhookResponse,
    WebhookStatus,
)
from app.utils.config import settings

logger = logging.getLogger(__name__)


async def forward_bounce(
    event_data: EventData, client: httpx.AsyncClient
) -> WebhookResponse:
    event_type = event_data.event

    # ignore if listmonk already tracks it
    if event_type not in [EventType.FAILED, EventType.COMPLAINED]:
        return WebhookResponse(
            webhook_status=WebhookStatus.IGNORED,
            error_code=WebhookErrorCode.EVENTTYPEIGNORED,
            message=f"Event '{event_type}' ignored",
        )

    # filter by tag to ensure it belongs to listmonk
    # not needed if you use different subdomains for
    # different apps
    if settings.REQUIRE_LISTMONK_TAG and "listmonk" not in event_data.tags:
        return WebhookResponse(
            webhook_status=WebhookStatus.IGNORED,
            error_code=WebhookErrorCode.NOTFROMLISTMONK,
            message="Not a Listmonk email",
        )

    mailgun_severity = event_data.severity

    listmonk_severity = ListmonkSeverity.HARD
    if mailgun_severity == EventSeverity.TEMPORARY:
        listmonk_severity = ListmonkSeverity.SOFT

    reasons = [
        event_data.delivery_status.message,
        event_data.delivery_status.description,
    ]
    error_msg = " | ".join(r for r in reasons if r) or "No reason provided"

    listmonk_error_msg = ListmonkMeta(reason=error_msg)

    listmonk_payload = ListmonkPayload(
        email=event_data.recipient, type=listmonk_severity, meta=listmonk_error_msg
    )

    # if you injected campaign id, then this will catch it
    if settings.ENABLE_CAMPAIGN_TRACKING and event_data.user_variables.campaign_uuid:
        listmonk_payload.campaign_uuid = event_data.user_variables.campaign_uuid

    try:
        response = await client.post(
            f"{settings.LISTMONK_URL}/webhooks/bounce",
            json=listmonk_payload.model_dump(exclude_none=True),
            auth=(settings.LISTMONK_API_USER, settings.LISTMONK_API_TOKEN),
            timeout=5.0,
        )
        response.raise_for_status()
    except httpx.RequestError as e:
        logger.error(f"Listmonk networking failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to reach Listmonk")
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Listmonk rejected payload. Status: {e.response.status_code}, Detail: {e.response.text}"
        )
        raise HTTPException(status_code=500, detail="Listmonk returned an error")

    return WebhookResponse(
        webhook_status=WebhookStatus.SUCCESS, message="Webhook forwarded"
    )
