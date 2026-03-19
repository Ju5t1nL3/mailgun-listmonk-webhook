from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException

from app.schemas import MailgunPayload
from app.services import forward_bounce
from app.utils.crypto import verify_mailgun_signature

app = FastAPI()


async def get_http_client():
    async with httpx.AsyncClient() as client:
        yield client


@app.post("/webhook")
async def receive_webhook(
    payload: MailgunPayload,
    client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> dict[str, str]:
    payload_signature = payload.signature
    if not verify_mailgun_signature(
        payload_signature.timestamp,
        payload_signature.token,
        payload_signature.signature,
    ):
        raise HTTPException(status_code=401, detail="Invalid Mailgun Signature")

    return await forward_bounce(payload.event_data, client)
