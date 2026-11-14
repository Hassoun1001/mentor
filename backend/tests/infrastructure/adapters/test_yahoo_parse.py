"""Yahoo chart adapter — how a raw chart response becomes price bars.

No network: the adapter is given an `httpx.MockTransport` that answers with
hand-built bodies shaped like Yahoo's v8 chart endpoint. Yahoo is the
always-available failover feed, and its payload is unofficial and messy
(null-padded slots, rounding that leaves high/low inside open/close), so the
parsing rules are pinned here rather than discovered in production.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import httpx
import pytest

from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.infrastructure.adapters.yahoo import YahooFinanceAdapter, YahooFinanceError

_START = datetime(2026, 6, 1, tzinfo=UTC)
_END = datetime(2026, 6, 2, tzinfo=UTC)


def _ts(year: int, month: int, day: int, hour: int) -> int:
    return int(datetime(year, month, day, hour, tzinfo=UTC).timestamp())


def _chart(timestamps: list[int], **quote: list[Any]) -> dict[str, Any]:
    return {
        "chart": {
            "result": [{"timestamp": timestamps, "indicators": {"quote": [quote]}}],
            "error": None,
        }
    }


def _adapter(body: dict[str, Any], seen: list[httpx.Request] | None = None) -> YahooFinanceAdapter:
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        return httpx.Response(200, json=body)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return YahooFinanceAdapter(client=client)


async def _bars(
    adapter: YahooFinanceAdapter, *, symbol: str = "EURUSD", timeframe: Timeframe = Timeframe.H1
) -> list[PriceBar]:
    return [
        b
        async for b in adapter.fetch_bars(
            symbol=symbol, timeframe=timeframe, start=_START, end=_END
        )
    ]


async def test_hourly_bars_are_parsed_and_the_request_uses_yahoo_conventions() -> None:
    seen: list[httpx.Request] = []
    body = _chart(
        [_ts(2026, 6, 1, 9), _ts(2026, 6, 1, 10)],
        open=[1.1000, 1.1010],
        high=[1.1020, 1.1030],
        low=[1.0990, 1.1000],
        close=[1.1010, 1.1025],
        volume=[0, 0],
    )
    bars = await _bars(_adapter(body, seen), symbol="eur/usd")

    assert len(seen) == 1
    assert seen[0].url.path.endswith("/EURUSD=X")
    assert seen[0].url.params["interval"] == "60m"
    assert seen[0].url.params["period1"] == str(int(_START.timestamp()))
    assert seen[0].url.params["period2"] == str(int(_END.timestamp()))

    assert [b.ts for b in bars] == [
        datetime(2026, 6, 1, 9, tzinfo=UTC),
        datetime(2026, 6, 1, 10, tzinfo=UTC),
    ]
    first = bars[0]
    assert first.symbol == "EUR/USD"
    assert first.source == "yahoo"
    assert first.timeframe is Timeframe.H1
    assert (first.open, first.high, first.low, first.close) == (
        Decimal("1.1"),
        Decimal("1.102"),
        Decimal("1.099"),
        Decimal("1.101"),
    )


async def test_null_padded_slots_are_skipped_not_filled() -> None:
    body = _chart(
        [_ts(2026, 6, 1, 9), _ts(2026, 6, 1, 10), _ts(2026, 6, 1, 11)],
        open=[1.10, None, 1.12],
        high=[1.11, 1.12, 1.13],
        low=[1.09, 1.10, None],
        close=[1.105, 1.115, 1.125],
    )
    bars = await _bars(_adapter(body))
    assert [b.ts.hour for b in bars] == [9]


async def test_short_quote_arrays_drop_the_bars_they_do_not_cover() -> None:
    body = _chart(
        [_ts(2026, 6, 1, 9), _ts(2026, 6, 1, 10)],
        open=[1.10, 1.11],
        high=[1.11, 1.12],
        low=[1.09, 1.10],
        close=[1.105],  # Yahoo cut the close series short
    )
    bars = await _bars(_adapter(body))
    assert [b.ts.hour for b in bars] == [9]


async def test_a_high_or_low_rounded_inside_the_body_is_widened_to_it() -> None:
    body = _chart(
        [_ts(2026, 6, 1, 9)],
        open=[1.1000],
        high=[1.1004],  # below the close
        low=[1.0999],
        close=[1.1005],
    )
    bars = await _bars(_adapter(body))
    assert bars[0].high == Decimal("1.1005")
    assert bars[0].low == Decimal("1.0999")

    body = _chart(
        [_ts(2026, 6, 1, 9)],
        open=[1.1000],
        high=[1.1010],
        low=[1.1002],  # above the open
        close=[1.1005],
    )
    bars = await _bars(_adapter(body))
    assert bars[0].low == Decimal("1.1")
    assert bars[0].high == Decimal("1.101")


@pytest.mark.parametrize(
    ("volume", "expected"),
    [
        ([2500], Decimal("2500")),
        ([0], None),  # FX on Yahoo reports 0: no real volume, not "nothing traded"
        ([None], None),
        ([], None),
    ],
)
async def test_volume_is_kept_only_when_yahoo_reports_one(
    volume: list[Any], expected: Decimal | None
) -> None:
    body = _chart(
        [_ts(2026, 6, 1, 9)], open=[1.10], high=[1.11], low=[1.09], close=[1.105], volume=volume
    )
    bars = await _bars(_adapter(body))
    assert bars[0].volume == expected


async def test_daily_bars_are_dated_on_the_utc_trading_day() -> None:
    # London midnight in summer is 23:00 UTC the day before.
    body = _chart([_ts(2026, 6, 21, 23)], open=[1.10], high=[1.11], low=[1.09], close=[1.105])
    seen: list[httpx.Request] = []
    bars = await _bars(_adapter(body, seen), timeframe=Timeframe.D1)
    assert seen[0].url.params["interval"] == "1d"
    assert bars[0].ts == datetime(2026, 6, 22, tzinfo=UTC)


@pytest.mark.parametrize(
    "body",
    [
        {"chart": {"result": None, "error": None}},
        {"chart": {"result": [], "error": None}},
        {"chart": {"result": [{"indicators": {"quote": [{}]}}], "error": None}},
        {},
    ],
)
async def test_an_empty_response_yields_no_bars(body: dict[str, Any]) -> None:
    assert await _bars(_adapter(body)) == []


async def test_an_error_payload_raises_instead_of_yielding_nothing() -> None:
    body = {"chart": {"result": None, "error": {"code": "Not Found", "description": "No data"}}}
    with pytest.raises(YahooFinanceError, match="Not Found"):
        await _bars(_adapter(body))


async def test_an_injected_client_is_not_closed_by_the_adapter() -> None:
    adapter = _adapter(_chart([]))
    await adapter.aclose()
    assert adapter._client.is_closed is False
