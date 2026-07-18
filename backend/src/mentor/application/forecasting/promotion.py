"""Champion/challenger model promotion.

The flywheel retrains as new resolved outcomes accumulate. But a retrain
is only an improvement if it *measurably* generalises better — otherwise
you're just overfitting to the latest noise. So every retrain produces
**challengers**, and the best challenger replaces the **champion** only
if its out-of-sample Brier score is lower by a margin. A worse model
never ships. This is the §13 "proof before trust" rule applied to the
model itself.

Two honesty upgrades over the naive version:

- **Candidate family, not a single roll.** Each retrain trains several
  configurations — technical-only, +macro, +news+macro — using whatever
  exogenous data is actually in the store, and grades them all on the
  same trailing test slice. The gate sees the best of the family.
- **Fair gate.** The champion's stored Brier was measured on the data of
  *its* era; comparing a fresh challenger against that number is
  apples-vs-oranges in a drifting market. Before deciding, the champion
  is re-graded on the **same** trailing window the challengers were
  tested on. Only when re-grading is impossible (model file gone) does
  the stored figure serve as fallback.

The champion pointer is a small JSON file in the model store so the live
loop and the forecast API can ask "which model is current?" without
unpickling anything.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from mentor.application.forecasting.news_context import build_news_by_ts, load_news_series
from mentor.application.macro.context import build_macro_by_ts, load_macro_series
from mentor.domain.errors import ValidationError
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.infrastructure.forecasting.model_store import ModelStore
from mentor.infrastructure.forecasting.sklearn_forecaster import (
    SklearnForecaster,
    evaluate_forecaster_on_tail,
    train_sklearn_forecaster,
)
from mentor.infrastructure.repositories.macro_series import MacroSeriesRepository
from mentor.infrastructure.repositories.news_tone import NewsToneRepository
from mentor.infrastructure.repositories.price_bars import PriceBarRepository
from mentor.logging import get_logger

log = get_logger("mentor.forecasting.promotion")

_CHAMPION_FILE = "champion.json"
_PROMOTIONS_FILE = "promotions.jsonl"  # append-only audit of every retrain decision
# A challenger must beat the champion's Brier by at least this much to ship.
_PROMOTION_MARGIN = 0.002
# Absolute floor: always answering "50%" scores a Brier of exactly 0.25, so a
# model that can't beat the coin flip (by the margin) has no business being
# champion — regardless of how bad the incumbent is. Without this floor a
# worse-than-random first champion could reign forever while the gate still
# called itself honest.
_COIN_FLIP_BRIER = 0.25
_BASELINE_FLOOR = _COIN_FLIP_BRIER - _PROMOTION_MARGIN


@dataclass(frozen=True, slots=True)
class PromotionResult:
    challenger_name: str
    challenger_brier: float
    champion_name: str | None
    champion_brier: float | None
    promoted: bool
    reason: str
    # Which feature family won, and how every candidate scored — the audit
    # trail that shows each learning cycle was a real search, not one roll.
    challenger_family: str = "technical"
    candidate_briers: dict[str, float] = field(default_factory=dict)
    # Champion re-graded on the same fresh test window (None = fallback used).
    champion_brier_fresh: float | None = None


def _to_domain(rows) -> list[PriceBar]:  # type: ignore[no-untyped-def]
    return [
        PriceBar(
            symbol=r.symbol,
            timeframe=Timeframe(r.timeframe),
            ts=r.ts,
            open=Decimal(r.open),
            high=Decimal(r.high),
            low=Decimal(r.low),
            close=Decimal(r.close),
            volume=Decimal(r.volume) if r.volume is not None else None,
            source=r.source,
        )
        for r in rows
    ]


class PromotionService:
    def __init__(
        self,
        *,
        model_store_dir: str | Path,
        prices: PriceBarRepository | None = None,
        news_tone: NewsToneRepository | None = None,
        macro: MacroSeriesRepository | None = None,
        news_query_key: str = "eurusd",
    ) -> None:
        # `prices` is only needed to retrain; reading the champion pointer
        # does not require a DB session, so it stays optional. `news_tone`
        # and `macro` unlock the exogenous candidate configurations when
        # their stores hold data.
        self._prices = prices
        self._news_tone = news_tone
        self._macro = macro
        self._news_query_key = news_query_key
        self._dir = Path(model_store_dir)
        self._store = ModelStore(model_store_dir)

    @property
    def _champion_path(self) -> Path:
        return self._dir / _CHAMPION_FILE

    def current_champion(self) -> dict[str, object] | None:
        if not self._champion_path.exists():
            return None
        data: dict[str, object] = json.loads(self._champion_path.read_text(encoding="utf-8"))
        return data

    @property
    def _promotions_path(self) -> Path:
        return self._dir / _PROMOTIONS_FILE

    def _log_decision(self, result: PromotionResult) -> None:
        """Append the retrain decision to the durable promotions audit log."""
        entry = {
            "at": datetime.now(UTC).isoformat(),
            "promoted": result.promoted,
            "challenger": result.challenger_name,
            "family": result.challenger_family,
            "challenger_brier": result.challenger_brier,
            "champion": result.champion_name,
            "champion_brier": result.champion_brier,
            "champion_brier_fresh": result.champion_brier_fresh,
            "candidates": result.candidate_briers,
            "reason": result.reason,
        }
        with self._promotions_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")

    def promotion_history(self, *, limit: int = 50) -> list[dict[str, object]]:
        """Most recent retrain decisions, newest first."""
        if not self._promotions_path.exists():
            return []
        lines = self._promotions_path.read_text(encoding="utf-8").splitlines()
        out: list[dict[str, object]] = []
        for line in reversed(lines[-limit:]):
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except ValueError:  # a torn write must not break the endpoint
                continue
        return out

    def _write_champion(self, *, name: str, brier: float, family: str) -> None:
        self._champion_path.write_text(
            json.dumps(
                {
                    "model_name": name,
                    "test_brier": brier,
                    "feature_family": family,
                    "promoted_at": datetime.now(UTC).isoformat(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    # ---- exogenous context (best effort — empty stores just narrow the family) ----

    async def _exogenous_context(
        self, bars: list[PriceBar]
    ) -> tuple[
        Mapping[datetime, Mapping[str, float]] | None,
        Mapping[datetime, Mapping[str, float]] | None,
    ]:
        timestamps = [b.ts for b in bars]
        news_by_ts: Mapping[datetime, Mapping[str, float]] | None = None
        if self._news_tone is not None:
            series = await load_news_series(self._news_tone, query_key=self._news_query_key)
            if not series.empty:
                news_by_ts = build_news_by_ts(series, timestamps)
        macro_by_ts: Mapping[datetime, Mapping[str, float]] | None = None
        if self._macro is not None:
            macro_series = await load_macro_series(self._macro)
            if not macro_series.empty:
                macro_by_ts = build_macro_by_ts(macro_series, timestamps)
        return news_by_ts, macro_by_ts

    def _regrade_champion(
        self,
        champion: dict[str, object],
        *,
        bars: list[PriceBar],
        horizon_bars: int,
        news_by_ts: Mapping[datetime, Mapping[str, float]] | None,
        macro_by_ts: Mapping[datetime, Mapping[str, float]] | None,
    ) -> float | None:
        """Champion Brier on the same fresh tail the challengers used."""
        name = str(champion.get("model_name") or "")
        if not name:
            return None
        try:
            model, _ = self._store.load(name)
        except (ValidationError, OSError, ValueError, KeyError) as exc:
            log.warning("promotion.champion_regrade_failed", name=name, error=str(exc))
            return None
        return evaluate_forecaster_on_tail(
            model,
            bars=bars,
            horizon_bars=horizon_bars,
            news_by_ts=news_by_ts,
            macro_by_ts=macro_by_ts,
        )

    def _decide_first_champion(
        self,
        *,
        challenger_name: str,
        challenger_brier: float,
        family: str,
        candidate_briers: dict[str, float],
        beats_floor: bool,
    ) -> PromotionResult:
        """No incumbent: install the challenger only if it clears the floor."""
        if beats_floor:
            self._write_champion(name=challenger_name, brier=challenger_brier, family=family)
            log.info("promotion.first_champion", name=challenger_name, brier=challenger_brier)
            reason = (
                f"No champion yet — challenger ({family}) Brier {challenger_brier:.4f} "
                f"beats the coin-flip floor {_BASELINE_FLOOR:.3f}; installed as champion."
            )
        else:
            log.info("promotion.floor_blocked", name=challenger_name, brier=challenger_brier)
            reason = (
                f"Challenger ({family}) Brier {challenger_brier:.4f} does not beat the "
                f"coin-flip floor {_BASELINE_FLOOR:.3f} — no champion installed; the "
                f"transparent baseline rule keeps predicting."
            )
        return PromotionResult(
            challenger_name=challenger_name,
            challenger_brier=challenger_brier,
            champion_name=None,
            champion_brier=None,
            promoted=beats_floor,
            reason=reason,
            challenger_family=family,
            candidate_briers=candidate_briers,
        )

    async def retrain_and_promote(
        self,
        *,
        symbol: str,
        timeframe: Timeframe,
        horizon_bars: int,
        max_bars: int | None = None,
    ) -> PromotionResult:
        if self._prices is None:
            raise ValidationError("retrain requires a price repository")
        rows = await self._prices.range(
            symbol=symbol,
            timeframe=timeframe,
            start=datetime(2000, 1, 1, tzinfo=UTC),
            end=datetime(2100, 1, 1, tzinfo=UTC),
        )
        bars = _to_domain(rows)
        if max_bars is not None and len(bars) > max_bars:
            # Newest window only: feature building is O(n²) in bar count and
            # the recent regime dominates predictive value at short horizons.
            bars = bars[-max_bars:]
        if len(bars) < 300:
            raise ValidationError(f"need at least 300 bars to retrain; have {len(bars)}")

        news_by_ts, macro_by_ts = await self._exogenous_context(bars)

        # Candidate family — every configuration the available data allows,
        # all graded on the identical trailing test slice by the trainer.
        # Training is minutes of pure CPU; run it in a worker thread so the
        # event loop (and with it the whole single-process API) stays
        # responsive while the loop retrains.
        candidates: list[tuple[str, SklearnForecaster]] = [
            (
                "technical",
                await asyncio.to_thread(
                    train_sklearn_forecaster, bars=bars, horizon_bars=horizon_bars
                ),
            ),
        ]
        if macro_by_ts is not None:
            candidates.append(
                (
                    "technical+macro",
                    await asyncio.to_thread(
                        train_sklearn_forecaster,
                        bars=bars,
                        horizon_bars=horizon_bars,
                        macro_by_ts=macro_by_ts,
                    ),
                )
            )
        if news_by_ts is not None:
            candidates.append(
                (
                    "technical+news+macro" if macro_by_ts is not None else "technical+news",
                    await asyncio.to_thread(
                        train_sklearn_forecaster,
                        bars=bars,
                        horizon_bars=horizon_bars,
                        news_by_ts=news_by_ts,
                        macro_by_ts=macro_by_ts,
                    ),
                )
            )

        candidate_briers = {fam: model.report.test_brier for fam, model in candidates}
        family, challenger = min(candidates, key=lambda c: c[1].report.test_brier)
        challenger_brier = challenger.report.test_brier
        log.info("promotion.candidates", briers=candidate_briers, winner=family)

        # Persist only the winning challenger — losers stay out of the store.
        stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        challenger_name = f"auto_{symbol.lower()}_{timeframe.value}_{stamp}"
        self._store.save(
            challenger,
            name=challenger_name,
            symbol=symbol,
            timeframe=timeframe.value,
        )

        # Absolute floor first: nobody ships without beating the coin flip.
        beats_floor = challenger_brier <= _BASELINE_FLOOR

        champion = self.current_champion()
        if champion is None:
            first = self._decide_first_champion(
                challenger_name=challenger_name,
                challenger_brier=challenger_brier,
                family=family,
                candidate_briers=candidate_briers,
                beats_floor=beats_floor,
            )
            self._log_decision(first)
            return first

        # Fair gate: champion re-graded on the same fresh window when possible.
        # Also CPU-bound (feature building + inference over the tail) — thread.
        champion_fresh = await asyncio.to_thread(
            self._regrade_champion,
            champion,
            bars=bars,
            horizon_bars=horizon_bars,
            news_by_ts=news_by_ts,
            macro_by_ts=macro_by_ts,
        )
        champion_stored = float(champion["test_brier"])  # type: ignore[arg-type]
        champion_brier = champion_fresh if champion_fresh is not None else champion_stored
        basis = "re-graded on the same fresh window" if champion_fresh is not None else "stored"

        improvement = champion_brier - challenger_brier
        if improvement >= _PROMOTION_MARGIN and beats_floor:
            self._write_champion(name=challenger_name, brier=challenger_brier, family=family)
            promoted = True
            reason = (
                f"Challenger ({family}) Brier {challenger_brier:.4f} beat champion "
                f"{champion_brier:.4f} ({basis}) by {improvement:.4f} "
                f"(≥ {_PROMOTION_MARGIN}) and clears the coin-flip floor — promoted."
            )
        elif improvement >= _PROMOTION_MARGIN and not beats_floor:
            promoted = False
            reason = (
                f"Challenger ({family}) Brier {challenger_brier:.4f} beat the champion "
                f"{champion_brier:.4f} ({basis}) but does not clear the coin-flip floor "
                f"{_BASELINE_FLOOR:.3f} — not promoted. Beating a bad incumbent is not "
                f"the same as being good."
            )
        else:
            promoted = False
            reason = (
                f"Challenger ({family}) Brier {challenger_brier:.4f} did not beat champion "
                f"{champion_brier:.4f} ({basis}) by the required {_PROMOTION_MARGIN} margin — "
                f"champion kept. A worse model never ships."
            )
        log.info(
            "promotion.decision",
            promoted=promoted,
            challenger=challenger_name,
            challenger_family=family,
            challenger_brier=challenger_brier,
            champion=champion.get("model_name"),
            champion_brier=champion_brier,
            champion_brier_basis=basis,
        )
        decision = PromotionResult(
            challenger_name=challenger_name,
            challenger_brier=challenger_brier,
            champion_name=str(champion.get("model_name")),
            champion_brier=champion_brier,
            promoted=promoted,
            reason=reason,
            challenger_family=family,
            candidate_briers=candidate_briers,
            champion_brier_fresh=champion_fresh,
        )
        self._log_decision(decision)
        return decision
