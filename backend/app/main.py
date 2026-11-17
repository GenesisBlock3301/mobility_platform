"""Application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import API_PREFIX, Settings, get_settings
from app.errors import install_error_handlers
from app.infra.db import create_engine, create_session_factory
from app.infra.rate_limit import FixedWindowLimiter
from app.logging import configure_logging
from app.middleware import RequestMiddleware
from app.routers.api import health, router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(settings.database_url.get_secret_value(), settings.db_timeout_seconds)
        app.state.session_factory = create_session_factory(engine)
        try:
            yield
        finally:
            await engine.dispose()

    app = FastAPI(
        title="Career Mobility API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.enable_docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.enable_docs else None,
    )
    app.state.limiter = FixedWindowLimiter()
    install_error_handlers(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.web_origin],
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["content-type"],
    )
    app.add_middleware(RequestMiddleware, settings=settings, limiter=app.state.limiter)
    app.include_router(health, prefix=API_PREFIX)
    app.include_router(router, prefix=API_PREFIX)
    return app
