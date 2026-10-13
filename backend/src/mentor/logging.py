"""Structured logging configuration.

Uses structlog over the stdlib logger so every log line is a single JSON
object in production and a colourised key/value line in development.
"""

from __future__ import annotations

import logging
import re
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from mentor.config import Settings


def _drop_color_message_key(_: object, __: str, event_dict: EventDict) -> EventDict:
    event_dict.pop("color_message", None)
    return event_dict


# Three providers take their secret in the request URL: Twelve Data
# (?apikey=), Finnhub (?token=) and Telegram (/bot<token>/ in the path).
# httpx logs every request URL at INFO, so a live audit found the Twelve Data
# key written to the server log every hour — and the Telegram token on every
# alert. Exception messages quote URLs too, so turning httpx down is not
# enough on its own: everything that reaches a log is scrubbed.
_SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"(?i)\b(apikey|api_key|token|access_token|key)=([^&\s\"'<>]+)"),
        r"\1=***",
    ),
    (re.compile(r"/bot\d+:[A-Za-z0-9_-]+"), "/bot***"),
)


def redact_secrets(text: str) -> str:
    """Replace credential values in URLs and query strings with ``***``."""
    for pattern, replacement in _SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _redact_event(_: object, __: str, event_dict: EventDict) -> EventDict:
    for key, value in event_dict.items():
        if isinstance(value, str):
            event_dict[key] = redact_secrets(value)
    return event_dict


class RedactingFilter(logging.Filter):
    """Scrub credentials from stdlib log records before any handler writes them."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        redacted = redact_secrets(message)
        if redacted != message:
            record.msg = redacted
            record.args = ()
        return True


def configure_logging(settings: Settings) -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        _drop_color_message_key,
        _redact_event,
        timestamper,
    ]

    if settings.is_production:
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[*shared_processors, structlog.processors.format_exc_info, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=settings.log_level.upper(),
    )

    for noisy in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(noisy).handlers.clear()
        logging.getLogger(noisy).propagate = True

    # One INFO line per outbound request, carrying the full URL — hourly noise
    # at best, a credential leak at worst. Warnings and errors still log.
    for chatty in ("httpx", "httpcore"):
        logging.getLogger(chatty).setLevel(logging.WARNING)

    # Filters on a *handler* see records propagated from every child logger;
    # a filter on the root logger itself would not.
    for handler in logging.getLogger().handlers:
        if not any(isinstance(f, RedactingFilter) for f in handler.filters):
            handler.addFilter(RedactingFilter())


def get_logger(name: str | None = None) -> Any:
    return structlog.get_logger(name)
