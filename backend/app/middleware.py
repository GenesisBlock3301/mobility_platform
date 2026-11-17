"""Request ID, access log, body-size limit, rate limit, security headers and the
last-resort error handler.

Written as plain ASGI middleware so it also wraps error responses.
"""

import logging
import secrets
import time
import uuid

from fastapi import HTTPException
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.config import API_PREFIX, Settings
from app.errors import problem
from app.infra.rate_limit import FixedWindowLimiter
from app.logging import request_id_var

logger = logging.getLogger("app.access")
error_logger = logging.getLogger("app.errors")

SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    (b"cache-control", b"no-store"),
]
DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
HEALTH_PREFIX = f"{API_PREFIX}/health"
TOO_LARGE = "The request body is too large."


class RequestMiddleware:
    def __init__(self, app: ASGIApp, settings: Settings, limiter: FixedWindowLimiter) -> None:
        self.app = app
        self.settings = settings
        self.limiter = limiter

    def client_key(self, scope: Scope) -> str:
        """Who to count a request against.

        Requests proven to come from the web server (internal token) carry
        x-client-key, which the web server derives from something the browser
        cannot forge per request (see frontend/lib/api.ts). Anything else is
        counted by its socket address.
        """
        headers = Headers(scope=scope)
        token = headers.get("x-internal-token")
        expected = self.settings.internal_token.get_secret_value()
        if token and secrets.compare_digest(token, expected):
            key = headers.get("x-client-key")
            if key:
                return f"web:{key[:80]}"
        client = scope.get("client")
        return client[0] if client else "unknown"

    def limited_receive(self, receive: Receive) -> Receive:
        """Count body bytes as they arrive, so chunked uploads without
        Content-Length are capped too."""
        received = 0
        limit = self.settings.max_body_bytes

        async def wrapper() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    raise HTTPException(413, TOO_LARGE)
            return message

        return wrapper

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid.uuid4().hex[:16]
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        state = {"status": 500, "started": False}
        method = scope["method"]
        path = scope["path"]

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                state["status"] = message["status"]
                state["started"] = True
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                if not path.startswith(DOCS_PATHS):
                    headers += SECURITY_HEADERS
                    headers.append(
                        (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'")
                    )
                message["headers"] = headers
            await send(message)

        try:
            length = Headers(scope=scope).get("content-length")
            if length and length.isdigit() and int(length) > self.settings.max_body_bytes:
                await problem(413, TOO_LARGE)(scope, receive, send_wrapper)
                return

            if (
                self.settings.rate_limit_enabled
                and path.startswith(f"{API_PREFIX}/")
                and not path.startswith(HEALTH_PREFIX)
            ):
                write = method in WRITE_METHODS
                limit = (
                    self.settings.rate_limit_writes_per_minute
                    if write
                    else self.settings.rate_limit_reads_per_minute
                )
                allowed, retry_after = self.limiter.hit(
                    self.client_key(scope), "write" if write else "read", limit
                )
                if not allowed:
                    response = problem(
                        429,
                        "Too many requests. Wait a moment and try again.",
                        headers={"Retry-After": str(retry_after)},
                    )
                    await response(scope, receive, send_wrapper)
                    return

            await self.app(scope, self.limited_receive(receive), send_wrapper)
        except Exception as exc:
            # Last resort, handled here rather than in Starlette's outer error
            # middleware so the response still gets the request ID and headers.
            error_logger.error("unhandled error", exc_info=exc)
            if not state["started"]:
                await problem(500, "Something went wrong on our side. Try again.")(
                    scope, receive, send_wrapper
                )
        finally:
            route = scope.get("route")
            logger.info(
                "request",
                extra={
                    "method": method,
                    # The route template, never the concrete path, so profile IDs stay out of logs.
                    "path": getattr(route, "path", "unmatched"),
                    "status": state["status"],
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                },
            )
            request_id_var.reset(token)
