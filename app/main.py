import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.route import router as webhook_router
from app.utils.config import Environment, settings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logging.getLogger("httpx").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
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

    app = FastAPI(
        lifespan=lifespan,
        docs_url=None if is_prod else "/docs",
        redoc_url=None if is_prod else "/redoc",
        openapi_url=None if is_prod else "/openapi.json",
    )

    app.include_router(webhook_router)

    return app


app = create_app()
