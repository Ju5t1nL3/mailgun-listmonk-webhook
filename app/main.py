import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, HTTPException, Request

from app.schemas import MailgunPayload, WebhookResponse
from app.services import forward_bounce
from app.utils.config import Environment, settings
from app.utils.crypto import verify_mailgun_signature

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logging.getLogger("httpx").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Initializes the global HTTP client pool in the application
    state. This ensures connection pooling across all requests
    and prevents socket exhaustion.
    """
    async with httpx.AsyncClient() as client:
        app.state.http_client = client
        yield


def create_app() -> FastAPI:
    is_prod = settings.ENVIRONMENT == Environment.PRODUCTION

    return FastAPI(
        lifespan=lifespan,
        docs_url=None if is_prod else "/docs",
        redoc_url=None if is_prod else "/redoc",
        openapi_url=None if is_prod else "/openapi.json",
    )


app = create_app()
