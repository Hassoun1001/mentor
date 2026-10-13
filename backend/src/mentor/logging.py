"""Structured logging configuration.

Uses structlog over the stdlib logger so every log line is a single JSON
object in production and a colourised key/value line in development.
"""

from __future__ import annotations

import logging
import re
import sys
import threading
from collections import Counter
from datetime import UTC, datetime
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


# ---- recurring-warning tally ------------------------------------------------

_TALLIED_LEVELS = frozenset({"warning", "error", "critical", "exception"})
_EVENT_KEY_MAX = 120


class LogTally:
    """Count warning-and-above log events by name since the process started.

    A degradation that recurs — GDELT rate limiting twice a day, the feed
    falling back to its second source — is invisible in a log nobody
    scrolls back through. The weekly self-report reads this so it shows up
    as a number instead. Process-lifetime by design: a restart resets it,
    and the snapshot says from when it counts.
    """

    def __init__(self) -> None:
        self._counts: Counter[tuple[str, str]] = Counter()
        self._since = datetime.now(UTC)
        self._lock = threading.Lock()

    def record(self, level: str, event: str) -> None:
        with self._lock:
            self._counts[(level, event[:_EVENT_KEY_MAX])] += 1

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            items = sorted(self._counts.items(), key=lambda kv: (-kv[1], kv[0]))
            return {
                "since": self._since.isoformat(),
                "events": [
                    {"level": level, "event": event, "count": count}
                    for (level, event), count in items
                ],
            }

    def reset(self) -> None:
        with self._lock:
            self._counts.clear()
            self._since = datetime.now(UTC)


_TALLY = LogTally()


def log_tally() -> LogTally:
    """The process-wide tally of recurring warnings and errors."""
    return _TALLY


def _tally_event(_: object, __: str, event_dict: EventDict) -> EventDict:
    level = str(event_dict.get("level", "")).lower()
    if level in _TALLIED_LEVELS:
        _TALLY.record(level, str(event_dict.get("event", "")))
    return event_dict


class TallyingFilter(logging.Filter):
    """Count stdlib warnings (apscheduler misfires and the like) by template.

    Keyed on the unformatted message so "job X missed by 2s" and "missed by
    3s" are one recurring event, not two — and so no argument value, which
    could carry a secret, ever becomes a key.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno >= logging.WARNING:
            _TALLY.record(record.levelname.lower(), f"{record.name}: {record.msg}")
        return True


def configure_logging(settings: Settings) -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        _drop_color_message_key,
        _redact_event,
        _tally_event,
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
        # Tally first, on the unformatted template, before redaction rewrites
        # the message.
        if not any(isinstance(f, TallyingFilter) for f in handler.filters):
            handler.addFilter(TallyingFilter())
        if not any(isinstance(f, RedactingFilter) for f in handler.filters):
            handler.addFilter(RedactingFilter())


def get_logger(name: str | None = None) -> Any:
    return structlog.get_logger(name)
