from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, HTTPException, Request

from app.schemas import MailgunPayload, WebhookResponse
from app.services import forward_bounce
from app.utils.crypto import verify_mailgun_signature


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Initializes the global HTTP client pool in the application state.
    This ensures connection pooling across all requests and prevents socket exhaustion.
    """
    async with httpx.AsyncClient() as client:
        app.state.http_client = client
        yield


app = FastAPI(lifespan=lifespan)


@app.post("/webhook", response_model=WebhookResponse)
async def receive_webhook(
    request: Request,
    payload: MailgunPayload,
) -> WebhookResponse:
    """
    Validates incoming mailgun webhook signatures and forwards the event to Listmonk.

    Raises:
        HTTPException(401): If the mailgun signature is invalid or missing
    """
    client = request.app.state.http_client

    payload_signature = payload.signature
    if not verify_mailgun_signature(
        payload_signature.timestamp,
        payload_signature.token,
        payload_signature.signature,
    ):
        raise HTTPException(status_code=401, detail="Invalid Mailgun Signature")

    return await forward_bounce(payload.event_data, client)
