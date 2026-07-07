"""Champion/challenger model promotion.

The flywheel retrains as new resolved outcomes accumulate. But a retrain
is only an improvement if it *measurably* generalises better — otherwise
you're just overfitting to the latest noise. So every retrain produces a
**challenger**, and the challenger replaces the **champion** only if its
out-of-sample Brier score (calibration on the trailing held-out slice)
is lower by a margin. A worse model never ships. This is the §13 "proof
before trust" rule applied to the model itself.

The champion pointer is a small JSON file in the model store so the live
loop and the forecast API can ask "which model is current?" without
unpickling anything.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from mentor.domain.errors import ValidationError
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.infrastructure.forecasting.model_store import ModelStore
from mentor.infrastructure.forecasting.sklearn_forecaster import train_sklearn_forecaster
from mentor.infrastructure.repositories.price_bars import PriceBarRepository
from mentor.logging import get_logger

log = get_logger("mentor.forecasting.promotion")

_CHAMPION_FILE = "champion.json"
# A challenger must beat the champion's Brier by at least this much to ship.
_PROMOTION_MARGIN = 0.002


@dataclass(frozen=True, slots=True)
class PromotionResult:
    challenger_name: str
    challenger_brier: float
    champion_name: str | None
    champion_brier: float | None
    promoted: bool
    reason: str


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
    ) -> None:
        # `prices` is only needed to retrain; reading the champion pointer
        # does not require a DB session, so it stays optional.
        self._prices = prices
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

    def _write_champion(self, *, name: str, brier: float) -> None:
        self._champion_path.write_text(
            json.dumps(
                {
                    "model_name": name,
                    "test_brier": brier,
                    "promoted_at": datetime.now(UTC).isoformat(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    async def retrain_and_promote(
        self,
        *,
        symbol: str,
        timeframe: Timeframe,
        horizon_bars: int,
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
        if len(bars) < 300:
            raise ValidationError(f"need at least 300 bars to retrain; have {len(bars)}")

        challenger = train_sklearn_forecaster(bars=bars, horizon_bars=horizon_bars)
        challenger_brier = challenger.report.test_brier
        stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        challenger_name = f"auto_{symbol.lower()}_{timeframe.value}_{stamp}"
        self._store.save(
            challenger,
            name=challenger_name,
            symbol=symbol,
            timeframe=timeframe.value,
        )

        champion = self.current_champion()
        if champion is None:
            self._write_champion(name=challenger_name, brier=challenger_brier)
            log.info("promotion.first_champion", name=challenger_name, brier=challenger_brier)
            return PromotionResult(
                challenger_name=challenger_name,
                challenger_brier=challenger_brier,
                champion_name=None,
                champion_brier=None,
                promoted=True,
                reason="No champion yet — challenger installed as the first champion.",
            )

        champion_brier = float(champion["test_brier"])  # type: ignore[arg-type]
        improvement = champion_brier - challenger_brier
        if improvement >= _PROMOTION_MARGIN:
            self._write_champion(name=challenger_name, brier=challenger_brier)
            promoted = True
            reason = (
                f"Challenger Brier {challenger_brier:.4f} beat champion "
                f"{champion_brier:.4f} by {improvement:.4f} (≥ {_PROMOTION_MARGIN}) — promoted."
            )
        else:
            promoted = False
            reason = (
                f"Challenger Brier {challenger_brier:.4f} did not beat champion "
                f"{champion_brier:.4f} by the required {_PROMOTION_MARGIN} margin — "
                f"champion kept. A worse model never ships."
            )
        log.info(
            "promotion.decision",
            promoted=promoted,
            challenger=challenger_name,
            challenger_brier=challenger_brier,
            champion=champion.get("model_name"),
            champion_brier=champion_brier,
        )
        return PromotionResult(
            challenger_name=challenger_name,
            challenger_brier=challenger_brier,
            champion_name=str(champion.get("model_name")),
            champion_brier=champion_brier,
            promoted=promoted,
            reason=reason,
        )
