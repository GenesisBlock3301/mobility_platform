"""One error shape for every failure, based on RFC 9457 problem details.

Responses never include stack traces or exception text from the server.
"""

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import InterfaceError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.logging import request_id_var
from app.services.errors import NotFoundError

logger = logging.getLogger("app.errors")

# Standard reason phrases in sentence case, with our own wording where it reads better.
TITLE_OVERRIDES = {422: "Validation failed"}


def title_for(status: int) -> str:
    try:
        return TITLE_OVERRIDES.get(status) or HTTPStatus(status).phrase.capitalize()
    except ValueError:
        return "Error"


def problem(
    status: int,
    detail: str,
    errors: list[dict[str, str]] | None = None,
    headers: dict[str, str] | None = None,
    resource: str | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": title_for(status),
        "status": status,
        "detail": detail,
        "request_id": request_id_var.get(),
    }
    if errors:
        body["errors"] = errors
    if resource:
        # Machine-readable: which resource a 404 refers to ("profile" or "opportunity").
        body["resource"] = resource
    return JSONResponse(body, status_code=status, headers=headers, media_type="application/problem+json")


def _field(loc: tuple[Any, ...]) -> str:
    parts = [str(p) for p in loc if p not in ("body", "query", "path")]
    return ".".join(parts) or "body"


def _message(error: dict[str, Any]) -> str:
    message = str(error.get("msg", "Invalid value"))
    return message.removeprefix("Value error, ")


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [{"field": _field(tuple(e.get("loc", ()))), "message": _message(e)} for e in exc.errors()]
        return problem(422, "One or more fields are invalid.", errors)

    @app.exception_handler(NotFoundError)
    async def _not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return problem(404, f"{exc.what} not found.", resource=exc.what.lower())

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else title_for(exc.status_code)
        return problem(exc.status_code, detail, headers=getattr(exc, "headers", None))

    @app.exception_handler(OperationalError)
    @app.exception_handler(InterfaceError)
    @app.exception_handler(OSError)  # includes ConnectionError, TimeoutError and DNS failures
    async def _database(_: Request, exc: Exception) -> JSONResponse:
        logger.error("database unavailable", exc_info=exc)
        return problem(503, "The service is temporarily unavailable. Try again shortly.")

    # Any other exception is caught by RequestMiddleware, which returns a 500
    # problem response with the request ID and security headers.
