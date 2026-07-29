"""CFTC Commitments of Traders — weekly speculative positioning, no key.

The one genuinely *orthogonal* input this system has. Price, technicals,
rates, the dollar index — all are transforms of, or drivers priced into,
the same tape. COT is different in kind: it is *who holds what*, reported
by the exchange. Large speculators (the "non-commercial" category in the
legacy report) crowding to one side is a positioning fact, not a price
fact, and extreme crowding has a long-documented tendency to precede
reversals as the crowd runs out of marginal buyers.

Whether that helps EUR/USD *direction* is exactly the open question — so
this feeds the same promotion gate as everything else and earns its place
or doesn't. What it is not is another slice of price.

**Point-in-time is the whole game with COT**, and the classic backtest bug.
The report covers positions as of **Tuesday** but is not published until
the following **Friday** at 3:30pm ET. Keying a feature to the Tuesday
would let the model see Friday's data on Tuesday — three days of leaked
future. So every observation here is dated at its **publication** date
(Tuesday + `_PUBLICATION_LAG`), and `MacroSeries.features_asof` — which
only ever reads points with ``day <= cutoff`` — then gives no-lookahead
for free, the same discipline the FRED series use.

Source: CFTC's public Socrata dataset ``6dca-aqww`` (legacy futures-only).
Probed live before writing (HTTP 200, ~10y weekly history for "EURO FX",
keyless) — the throwaway-probe rule from the handover.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx

from mentor.domain.errors import DomainError
from mentor.domain.forecasting.macro_features import COT_EUR_SERIES_ID
from mentor.infrastructure.adapters.macro.fred import MacroObservation
from mentor.logging import get_logger

log = get_logger("mentor.adapters.cftc_cot")

_BASE = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"

# Tuesday report -> Friday 3:30pm ET release. We date observations four days
# on so the value is not visible until the Saturday *after* release: strictly
# safe for both the hourly and daily lanes (a Friday intraday bar can never
# peek at a report that only lands Friday afternoon), at the cost of one extra
# day of latency on a signal that moves weekly. Safety is the cheaper side of
# that trade.
_PUBLICATION_LAG = timedelta(days=4)

# Exact contract name — the unqualified "EURO FX", not the "EURO FX/BRITISH
# POUND XRATE" cross that also matches a prefix filter.
_EUR_CONTRACT = "EURO FX"

# The series id lives in the domain (macro_features); imported above so the
# adapter and the feature computation cannot drift apart.


class CftcError(DomainError):
    """CFTC request failed or returned an unusable response."""


def _to_float(row: dict[str, object], key: str) -> float | None:
    raw = row.get(key)
    if raw is None:
        return None
    try:
        return float(raw)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return None


def parse_rows(rows: list[dict[str, object]], *, series_id: str) -> list[MacroObservation]:
    """Turn raw CFTC rows into publication-dated net-positioning observations.

    The value is large-speculator **net** position as a fraction of open
    interest: ``(noncomm_long - noncomm_short) / open_interest``. Bounded,
    roughly stationary, and sign-carrying — positive means specs are net
    long. Rows missing any leg, or with non-positive open interest, are
    skipped rather than guessed.

    CFTC publishes more than one instrument under the "EURO FX" name (distinct
    contract market codes across venues), so several rows can share a report
    date. Storing both would collide on ``(series_id, day)`` — and did, on the
    first live ingest. We keep the **dominant** contract per day, the one with
    the most open interest, which is the one whose positioning actually moves
    the pair.
    """
    by_day: dict[datetime, tuple[float, float]] = {}  # published day -> (net%OI, OI)
    for row in rows:
        raw_day = row.get("report_date_as_yyyy_mm_dd")
        long_ = _to_float(row, "noncomm_positions_long_all")
        short_ = _to_float(row, "noncomm_positions_short_all")
        oi = _to_float(row, "open_interest_all")
        if not isinstance(raw_day, str) or long_ is None or short_ is None or oi is None:
            continue
        if oi <= 0:
            continue
        try:
            report_day = datetime.fromisoformat(raw_day.replace("Z", "+00:00"))
        except ValueError:
            continue
        if report_day.tzinfo is None:
            report_day = report_day.replace(tzinfo=UTC)
        published = report_day + _PUBLICATION_LAG
        prior = by_day.get(published)
        if prior is None or oi > prior[1]:
            by_day[published] = ((long_ - short_) / oi, oi)
    out = [
        MacroObservation(series_id=series_id, day=day, value=net)
        for day, (net, _oi) in by_day.items()
    ]
    out.sort(key=lambda o: o.day)
    return out


class CftcCotAdapter:
    """Fetches the full COT history for one futures contract."""

    def __init__(
        self,
        *,
        contract_market_name: str = _EUR_CONTRACT,
        series_id: str = COT_EUR_SERIES_ID,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._contract = contract_market_name
        self._series_id = series_id
        self._client = client
        self._owns_client = client is None

    async def __aenter__(self) -> CftcCotAdapter:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=40)
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()

    async def fetch(self) -> list[MacroObservation]:
        assert self._client is not None
        params = {
            "$where": f"contract_market_name = '{self._contract}'",
            "$select": (
                "report_date_as_yyyy_mm_dd,noncomm_positions_long_all,"
                "noncomm_positions_short_all,open_interest_all"
            ),
            "$order": "report_date_as_yyyy_mm_dd ASC",
            "$limit": "5000",
        }
        try:
            resp = await self._client.get(_BASE, params=params)
        except httpx.HTTPError as exc:
            raise CftcError(f"CFTC request failed: {exc}") from exc
        if resp.status_code != 200:
            raise CftcError(f"CFTC returned {resp.status_code}")
        try:
            rows = resp.json()
        except ValueError as exc:
            raise CftcError("CFTC returned non-JSON") from exc
        if not isinstance(rows, list):
            raise CftcError("CFTC returned an unexpected shape")
        obs = parse_rows(rows, series_id=self._series_id)
        log.info("cftc_cot.fetched", contract=self._contract, rows=len(obs))
        return obs
