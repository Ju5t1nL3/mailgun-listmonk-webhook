import json

import httpx
from fastapi import HTTPException

from app.schemas import EventData, EventSeverity, EventType
from app.utils.config import settings


async def forward_bounce(event_data: EventData) -> dict[str, str]:
    event_type = event_data.event

    # ignore if listmonk already tracks it
    if event_type not in [EventType.FAILED, EventType.COMPLAINED]:
        return {"status": "ignored", "reason": f"Event '{event_type}' ignored"}

    # filter by tag to ensure it belongs to listmonk
    # not needed if you use different subdomains for
    # different apps

    # uncomment this block if you only use one domain
    # for all email sending
    # if "listmonk" not in event_data.tags:
    #     return {"status": "ignored", "reason": "Not a Listmonk email"}

    mailgun_severity = event_data.severity

    listmonk_severity = "hard"
    if mailgun_severity == EventSeverity.TEMPORARY:
        listmonk_severity = "soft"

    reasons = [
        event_data.delivery_status.message,
        event_data.delivery_status.description,
    ]
    error_msg = " | ".join(r for r in reasons if r) or "No reason provided"

    listmonk_payload = {
        "email": event_data.recipient,
        "source": "mailgun_webhook",
        "type": listmonk_severity,
        "meta": json.dumps({"reason": error_msg}),
    }

    # if you injected campaign id, then this will catch it
    campaign_uuid = event_data.user_variables.campaign_uuid
    if campaign_uuid:
        listmonk_payload["campaign_uuid"] = campaign_uuid

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.LISTMONK_URL}/webhooks/bounce",
                json=listmonk_payload,
                auth=(settings.LISTMONK_API_USER, settings.LISTMONK_API_TOKEN),
                timeout=5.0,
            )
            response.raise_for_status()
    except httpx.RequestError as e:
        print(f"Listmonk networking failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to reach Listmonk")
    except httpx.HTTPStatusError as e:
        print(f"Listmonk rejected payload: {e}")
        raise HTTPException(status_code=500, detail="Listmonk returned an error")

    return {"status": "success", "message": "Webhook forwarded"}
