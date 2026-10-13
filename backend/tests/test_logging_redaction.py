"""Secrets must never reach a log line.

Twelve Data, Finnhub and Telegram all take their credential in the request
URL, and httpx logs every request URL at INFO. A live audit found the Twelve
Data key in the server log every hour. These tests pin the scrubbing.
Values below are fabricated shapes, not real credentials.
"""

from __future__ import annotations

import logging

from mentor.config import Settings
from mentor.logging import RedactingFilter, _redact_event, configure_logging, redact_secrets

_TD_URL = (
    "GET https://api.twelvedata.com/time_series?symbol=EUR%2FUSD&interval=1h"
    "&apikey=0123456789abcdef0123456789abcdef&format=JSON"
)


def test_a_query_string_key_is_replaced_and_everything_else_kept() -> None:
    out = redact_secrets(_TD_URL)
    assert "0123456789abcdef" not in out
    assert "apikey=***" in out
    assert "symbol=EUR%2FUSD" in out  # non-secret parameters survive
    assert out.endswith("&format=JSON")


def test_finnhub_style_token_is_replaced() -> None:
    out = redact_secrets("https://finnhub.io/api/v1/calendar/economic?from=x&token=abcDEF123xyz")
    assert "abcDEF123xyz" not in out
    assert "token=***" in out


def test_telegram_bot_token_in_the_path_is_replaced() -> None:
    out = redact_secrets("POST https://api.telegram.org/bot123456789:AAFakeToken_value-XYZ/sendMessage")
    assert "AAFakeToken" not in out
    assert "/bot***/sendMessage" in out


def test_ordinary_text_is_left_alone() -> None:
    text = "monkey=3 and the key features were vol_20 and token_count"
    assert redact_secrets(text) == text


def test_stdlib_records_are_scrubbed_including_formatting_args() -> None:
    record = logging.LogRecord(
        "httpx", logging.WARNING, __file__, 1, "HTTP Request: %s %s", ("GET", _TD_URL), None
    )
    assert RedactingFilter().filter(record) is True
    assert "0123456789abcdef" not in record.getMessage()
    assert "apikey=***" in record.getMessage()


def test_structlog_event_values_are_scrubbed() -> None:
    event = {"event": "fetch failed", "error": f"Client error for url {_TD_URL}", "rows": 3}
    out = _redact_event(None, "warning", event)
    assert "0123456789abcdef" not in out["error"]
    assert out["rows"] == 3


def test_configure_logging_silences_request_lines_and_installs_the_filter() -> None:
    configure_logging(Settings(_env_file=None))  # type: ignore[call-arg]
    assert logging.getLogger("httpx").getEffectiveLevel() >= logging.WARNING
    assert logging.getLogger("httpcore").getEffectiveLevel() >= logging.WARNING
    root_handlers = logging.getLogger().handlers
    assert root_handlers
    assert all(
        any(isinstance(f, RedactingFilter) for f in h.filters) for h in root_handlers
    )
