"""CFTC COT ingestion — cache weekly speculative positioning.

Pulls the full Euro FX Commitments-of-Traders history and upserts it into
the same ``macro_series`` cache the FRED drivers use, so the trainer and
forecaster consume it through the existing point-in-time path with no new
plumbing. Idempotent on ``(series_id, day)``, so it is safe to schedule
weekly — a re-run overwrites the same rows.

Mirrors ``macro.ingest.MacroIngestService``.
"""

from __future__ import annotations

from dataclasses import dataclass

from mentor.domain.forecasting.macro_features import COT_EUR_SERIES_ID
from mentor.infrastructure.adapters.macro.cftc_cot import CftcCotAdapter
from mentor.infrastructure.repositories.macro_series import MacroSeriesRepository
from mentor.logging import get_logger

log = get_logger("mentor.macro.cot_ingest")


@dataclass(frozen=True, slots=True)
class CotIngestResult:
    series_id: str
    observations_fetched: int
    rows_written: int


class CotIngestService:
    def __init__(
        self,
        *,
        repo: MacroSeriesRepository,
        adapter: CftcCotAdapter | None = None,
    ) -> None:
        self._repo = repo
        self._adapter = adapter

    async def backfill(self) -> CotIngestResult:
        """Fetch the full COT history and upsert it. No date range: the whole
        series is ~1,500 weekly rows, cheaper to refresh whole than to reason
        about incremental windows around the Tuesday/Friday publication gap."""
        adapter = self._adapter or CftcCotAdapter()
        async with adapter as a:
            observations = await a.fetch()
        written = await self._repo.upsert(observations)
        log.info(
            "cot_ingest.done",
            fetched=len(observations),
            written=written,
        )
        return CotIngestResult(
            series_id=COT_EUR_SERIES_ID,
            observations_fetched=len(observations),
            rows_written=written,
        )
