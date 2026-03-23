from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, HTTPException, Request

from app.schemas import MailgunPayload, WebhookResponse
from app.services import forward_bounce
from app.utils.crypto import verify_mailgun_signature


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with httpx.AsyncClient() as client:
        app.state.http_client = client
        yield


app = FastAPI(lifespan=lifespan)


@app.post("/webhook", response_model=WebhookResponse)
async def receive_webhook(
    request: Request,
    payload: MailgunPayload,
):
    client = request.app.state.http_client

    payload_signature = payload.signature
    if not verify_mailgun_signature(
        payload_signature.timestamp,
        payload_signature.token,
        payload_signature.signature,
    ):
        raise HTTPException(status_code=401, detail="Invalid Mailgun Signature")

    return await forward_bounce(payload.event_data, client)
