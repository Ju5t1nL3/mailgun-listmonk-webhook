import json

import requests
from fastapi import HTTPException

from app.schemas import EventData, EventSeverity, EventType
from app.utils.config import settings


def forward_bounce(event_data: EventData) -> dict[str, str]:
    event_type = event_data.event

    # ignore if listmonk already tracks it
    if event_type not in [EventType.FAILED, EventType.COMPLAINED]:
        return {"status": "ignored", "reason": f"Event '{event_type}' ignored"}

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

    try:
        response = requests.post(
            f"{settings.LISTMONK_URL}/webhooks/bounce",
            json=listmonk_payload,
            auth=(settings.LISTMONK_API_USER, settings.LISTMONK_API_TOKEN),
            timeout=5,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Listmonk forwarding failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to forward to Listmonk")

    return {"status": "success", "message": "Webhook forwarded"}
