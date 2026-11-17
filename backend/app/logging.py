"""JSON log lines. Request bodies and profile fields are never logged."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

# Only these extra attributes are copied into a log line. Anything else passed
# in `extra` is dropped, so profile data cannot leak into logs by accident.
ALLOWED_FIELDS = ("method", "path", "status", "duration_ms", "client", "event")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        line = {
            "time": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        for name in ALLOWED_FIELDS:
            if hasattr(record, name):
                line[name] = getattr(record, name)
        if record.exc_info:
            line["error"] = record.exc_info[0].__name__ if record.exc_info[0] else "Exception"
        return json.dumps(line)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    # Uvicorn's own access log would print full paths, including profile IDs.
    logging.getLogger("uvicorn.access").disabled = True
