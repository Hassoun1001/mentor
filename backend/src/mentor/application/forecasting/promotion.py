"""Champion/challenger model promotion.

The flywheel retrains as new resolved outcomes accumulate. But a retrain
is only an improvement if it *measurably* generalises better — otherwise
you're just overfitting to the latest noise. So every retrain produces
**challengers**, and the best challenger replaces the **champion** only
if its out-of-sample Brier score is lower by a margin. A worse model
never ships. This is the §13 "proof before trust" rule applied to the
model itself.

The gate's honesty machinery, in order of adoption:

- **Fair gate.** The champion is re-graded on the *same* fresh trailing
  window the challenger was tested on — never compared via its stale
  stored score from a different market era.
- **Coin-flip floor.** Nothing installs or promotes without beating the
  0.25 Brier of always answering "50%" (by the margin). Beating a bad
  incumbent is not the same as being good.
- **Breakeven floor.** Brier says the probabilities are honest; it cannot
  say whether acting on them pays, because it knows nothing about the
  spread. So the challenger's hit rate on the hours it acts must also
  clear the lane's measured breakeven — 52.36% on the 24-bar lane,
  50.73% on the 5-day one. Being better than a coin is not the same as
  being worth trading.
- **Demotion with hysteresis.** An incumbent whose *fresh* re-grade fails
  the floor on several consecutive retrains loses the crown — the
  transparent baseline rule predicts until someone genuinely earns it.
  One passing re-grade resets the streak, so a single rough window
  can't dethrone anyone (no flapping).
- **Walk-forward candidate selection.** The winning configuration is
  chosen by its mean Brier across sequential validation folds carved
  from *pre-tail* history — not by one lucky roll on a single split.
  The final gate tail stays untouched by selection.
- **Lessons.** Every retrain writes what it learned (live post-mortem
  metrics, feature importances, the decision) to a durable log; the
  "pruned" candidate reads recent lessons to drop dead-weight features.
  The feedback loop can only ship improvements through the same gate.

The champion pointer is a small JSON file in the model store so the live
loop and the forecast API can ask "which model is current?" without
unpickling anything.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from mentor.application.forecasting.economics import round_trip_cost_price
from mentor.application.forecasting.htf_context import (
    HTF_TIMEFRAME,
    build_htf_by_ts,
    load_htf_series,
)
from mentor.application.forecasting.news_context import build_news_by_ts, load_news_series
from mentor.application.forecasting.postmortem import compute_post_mortem
from mentor.application.macro.context import build_macro_by_ts, load_macro_series
from mentor.domain.errors import ValidationError
from mentor.domain.forecasting.features import FEATURE_NAMES
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.domain.stats.breakeven import BreakevenBasis, estimate_breakeven
from mentor.infrastructure.forecasting.model_store import ModelStore
from mentor.infrastructure.forecasting.sklearn_forecaster import (
    SklearnForecaster,
    TrainingReport,
    evaluate_policy_on_tail,
    train_sklearn_forecaster,
)
from mentor.infrastructure.repositories.macro_series import MacroSeriesRepository
from mentor.infrastructure.repositories.news_tone import NewsToneRepository
from mentor.infrastructure.repositories.predictions import PredictionRepository
from mentor.infrastructure.repositories.price_bars import PriceBarRepository
from mentor.logging import get_logger

log = get_logger("mentor.forecasting.promotion")

_CHAMPION_FILE = "champion.json"
_PROMOTIONS_FILE = "promotions.jsonl"  # append-only audit of every retrain decision
_LESSONS_FILE = "lessons.jsonl"  # what each retrain learned (postmortem + importances)
# A challenger must beat the champion's Brier by at least this much to ship.
_PROMOTION_MARGIN = 0.002
# Absolute floor: always answering "50%" scores a Brier of exactly 0.25, so a
# model that can't beat the coin flip (by the margin) has no business being
# champion — regardless of how bad the incumbent is.
_COIN_FLIP_BRIER = 0.25
_BASELINE_FLOOR = _COIN_FLIP_BRIER - _PROMOTION_MARGIN
# A challenger that abstains on almost everything can post a great covered
# Brier off a handful of lucky hours. It must be willing to speak this often.
_MIN_COVERAGE = 0.15
# Demote the incumbent after this many CONSECUTIVE fresh-window floor
# failures. Hysteresis: one passing re-grade resets the streak.
_DEMOTION_AFTER = 3
# Walk-forward selection folds: each value is a prefix fraction of the bars;
# the trainer's own trailing test slice inside that prefix is the fold's
# validation window. Both folds end before the final gate tail begins.
_SELECTION_FOLDS = (0.64, 0.80)
# The lessons-driven pruned candidate keeps at least this many technical
# features; below the threshold share of total importance a feature is
# considered dead weight.
_PRUNE_MIN_FEATURES = 6
_PRUNE_SHARE = 0.02
# Fallback compact set used before any lessons exist (canonical order).
_STATIC_COMPACT = (
    "ret_5",
    "ret_10",
    "ema_slow_dist",
    "ema_fast_minus_slow",
    "rsi_14",
    "atr_pct",
    "high_20_dist",
    "low_20_dist",
    "vol_20",
)


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
    # The incumbent lost the crown after repeated floor failures.
    demoted: bool = False
    # The economic floor: what a call had to clear to pay for itself on this
    # lane, and what the challenger actually managed. Recorded on every
    # decision so the audit trail shows the bar, not just the verdict.
    breakeven: float = 0.5
    challenger_accuracy: float = 0.0


def clears_floors(
    report: TrainingReport,
    *,
    brier: float,
    economics: BreakevenBasis,
) -> tuple[bool, str]:
    """The absolute floors a challenger must clear, and which one stopped it.

    Three separate questions, deliberately not merged:

    1. **Calibrated?** Brier on the hours it acts must beat the 0.25 of
       always answering "50%", by the promotion margin.
    2. **Willing to speak?** A model that abstains its way down to a
       handful of lucky hours can post a beautiful covered Brier.
    3. **Worth trading?** Its hit rate must clear the lane's measured
       breakeven. This is the one that was missing: Brier knows nothing
       about the spread, so a model could be honestly calibrated, clear
       0.248, be right 51% of the time, and lose money on every call.

    Returns the verdict and a sentence naming the binding floor — "failed
    the gate" with three gates behind it tells nobody what to fix.
    """
    enough_coverage = not report.abstains or report.coverage >= _MIN_COVERAGE

    # An unmeasurable hurdle (too few non-overlapping windows) falls back to
    # the other two floors. That is the status quo rather than a loosening:
    # blocking every promotion on a number we cannot compute would freeze the
    # loop, not protect it.
    accuracy = report.effective_accuracy
    pays_for_itself = not economics.measured or accuracy >= economics.breakeven

    passed = brier <= _BASELINE_FLOOR and enough_coverage and pays_for_itself

    if not pays_for_itself:
        detail = (
            f" Its hit rate on the hours it acts ({accuracy * 100:.1f}%) is below the "
            f"{economics.breakeven * 100:.2f}% needed to cover the spread — acting on "
            f"it would lose money even where it is right more often than not."
        )
    elif not enough_coverage:
        detail = (
            f" It abstains on all but {report.coverage * 100:.0f}% of hours, below the "
            f"{_MIN_COVERAGE * 100:.0f}% a champion must be willing to speak on."
        )
    else:
        detail = ""
    return passed, detail


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


def _read_jsonl_tail(path: Path, limit: int) -> list[dict[str, object]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[dict[str, object]] = []
    for line in reversed(lines[-limit:]):
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except ValueError:  # a torn write must not break the endpoint
            continue
    return out


class PromotionService:
    def __init__(
        self,
        *,
        model_store_dir: str | Path,
        prices: PriceBarRepository | None = None,
        news_tone: NewsToneRepository | None = None,
        macro: MacroSeriesRepository | None = None,
        news_query_key: str = "eurusd",
        predictions: PredictionRepository | None = None,
    ) -> None:
        # `prices` is only needed to retrain; reading the champion pointer
        # does not require a DB session, so it stays optional. `news_tone`
        # and `macro` unlock the exogenous candidate configurations when
        # their stores hold data; `predictions` lets each retrain record the
        # live post-mortem in its lesson.
        self._prices = prices
        self._news_tone = news_tone
        self._macro = macro
        self._news_query_key = news_query_key
        self._predictions = predictions
        self._dir = Path(model_store_dir)
        self._store = ModelStore(model_store_dir)

    # ---- champion pointer -------------------------------------------------

    @property
    def _champion_path(self) -> Path:
        return self._dir / _CHAMPION_FILE

    def current_champion(self) -> dict[str, object] | None:
        if not self._champion_path.exists():
            return None
        data: dict[str, object] = json.loads(self._champion_path.read_text(encoding="utf-8"))
        return data

    def _write_champion(
        self, *, name: str, brier: float, family: str, floor_failures: int = 0
    ) -> None:
        self._champion_path.write_text(
            json.dumps(
                {
                    "model_name": name,
                    "test_brier": brier,
                    "feature_family": family,
                    "promoted_at": datetime.now(UTC).isoformat(),
                    "floor_failures": floor_failures,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    # ---- durable logs -----------------------------------------------------

    @property
    def _promotions_path(self) -> Path:
        return self._dir / _PROMOTIONS_FILE

    @property
    def _lessons_path(self) -> Path:
        return self._dir / _LESSONS_FILE

    def _log_decision(self, result: PromotionResult) -> None:
        """Append the retrain decision to the durable promotions audit log."""
        entry = {
            "at": datetime.now(UTC).isoformat(),
            "promoted": result.promoted,
            "demoted": result.demoted,
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
        return _read_jsonl_tail(self._promotions_path, limit)

    def lessons_history(self, *, limit: int = 50) -> list[dict[str, object]]:
        """What recent retrains learned, newest first."""
        return _read_jsonl_tail(self._lessons_path, limit)

    async def _log_lesson(
        self,
        result: PromotionResult,
        challenger: SklearnForecaster,
        selection_briers: dict[str, float],
    ) -> None:
        """Persist what this retrain learned — the feedback loop's memory."""
        live: dict[str, float | int] | None = None
        if self._predictions is not None:
            rows = await self._predictions.list_resolved(limit=500)
            pm = compute_post_mortem(rows)
            live = {
                "n_resolved": pm.sample_size,
                "directional": pm.directional,
                "accuracy": round(pm.directional_accuracy, 4),
                "brier": round(pm.brier_score, 4),
                "ece": round(pm.ece, 4),
            }
        top = sorted(
            challenger.report.feature_importances.items(), key=lambda kv: kv[1], reverse=True
        )
        entry = {
            "at": datetime.now(UTC).isoformat(),
            "promoted": result.promoted,
            "demoted": result.demoted,
            "family": result.challenger_family,
            "challenger_brier": result.challenger_brier,
            "champion_brier_fresh": result.champion_brier_fresh,
            "selection": selection_briers,
            "importances": {k: round(v, 6) for k, v in top},
            "live": live,
        }
        with self._lessons_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")

    # ---- lessons-driven pruning -------------------------------------------

    def _pruned_features(self) -> tuple[str, ...]:
        """Technical-feature subset for the pruned candidate.

        Averages permutation importances over the last few lessons and drops
        features that carried under ``_PRUNE_SHARE`` of the total — dead
        weight that only adds variance. Before any lessons exist, a static
        compact set stands in. Never returns fewer than
        ``_PRUNE_MIN_FEATURES`` features.
        """
        lessons = [e for e in self.lessons_history(limit=3) if e.get("importances")]
        if not lessons:
            return _STATIC_COMPACT
        totals: dict[str, float] = dict.fromkeys(FEATURE_NAMES, 0.0)
        for entry in lessons:
            imps = entry.get("importances")
            if not isinstance(imps, dict):
                continue
            for name in FEATURE_NAMES:
                value = imps.get(name)
                if isinstance(value, (int, float)):
                    totals[name] += float(value)
        grand = sum(totals.values())
        if grand <= 0:
            return _STATIC_COMPACT
        kept = tuple(n for n in FEATURE_NAMES if totals[n] / grand >= _PRUNE_SHARE)
        if len(kept) < _PRUNE_MIN_FEATURES:
            ranked = sorted(FEATURE_NAMES, key=lambda n: totals[n], reverse=True)
            kept = tuple(sorted(ranked[:_PRUNE_MIN_FEATURES], key=FEATURE_NAMES.index))
        return kept

    # ---- exogenous context (best effort — empty stores just narrow the family) ----

    async def _exogenous_context(
        self, bars: list[PriceBar], symbol: str = "EURUSD"
    ) -> tuple[
        Mapping[datetime, Mapping[str, float]] | None,
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
        # Higher-timeframe (daily) context — only meaningful for an intraday
        # lane; a daily model looking "up" at itself would be circular.
        htf_by_ts: Mapping[datetime, Mapping[str, float]] | None = None
        if self._prices is not None and bars and bars[0].timeframe is not HTF_TIMEFRAME:
            htf_series = await load_htf_series(self._prices, symbol=symbol)
            if not htf_series.empty:
                htf_by_ts = build_htf_by_ts(htf_series, timestamps)
        return news_by_ts, macro_by_ts, htf_by_ts

    # ---- candidate configurations -----------------------------------------

    def _candidate_configs(
        self,
        news_by_ts: Mapping[datetime, Mapping[str, float]] | None,
        macro_by_ts: Mapping[datetime, Mapping[str, float]] | None,
        htf_by_ts: Mapping[datetime, Mapping[str, float]] | None = None,
    ) -> list[tuple[str, dict[str, Any]]]:
        configs: list[tuple[str, dict[str, Any]]] = [("technical", {})]
        if macro_by_ts is not None:
            configs.append(("technical+macro", {"macro_by_ts": macro_by_ts}))
        if news_by_ts is not None:
            name = "technical+news+macro" if macro_by_ts is not None else "technical+news"
            kwargs: dict[str, Any] = {"news_by_ts": news_by_ts}
            if macro_by_ts is not None:
                kwargs["macro_by_ts"] = macro_by_ts
            configs.append((name, kwargs))
        # A more conservative learner — shallower, more regularised. Same
        # feature set as the strongest exogenous config available.
        reg_kwargs: dict[str, Any] = {
            "classifier_params": {"max_depth": 3, "l2_regularization": 4.0, "max_iter": 150}
        }
        if macro_by_ts is not None:
            reg_kwargs["macro_by_ts"] = macro_by_ts
        configs.append(("regularized" + ("+macro" if macro_by_ts is not None else ""), reg_kwargs))
        # Lessons-driven pruned feature set (falls back to a static compact
        # set before lessons exist). Skip if pruning changes nothing.
        pruned = self._pruned_features()
        if set(pruned) != set(FEATURE_NAMES):
            pr_kwargs: dict[str, Any] = {"technical_features": pruned}
            if macro_by_ts is not None:
                pr_kwargs["macro_by_ts"] = macro_by_ts
            configs.append(("pruned" + ("+macro" if macro_by_ts is not None else ""), pr_kwargs))
        # Multi-timeframe: give the intraday model the daily picture. Added as
        # its own candidates so the gate measures whether it actually helps
        # rather than assuming it does.
        if htf_by_ts is not None:
            configs.append(("technical+htf", {"htf_by_ts": htf_by_ts}))
            if macro_by_ts is not None:
                configs.append(
                    ("technical+macro+htf", {"macro_by_ts": macro_by_ts, "htf_by_ts": htf_by_ts})
                )
        return configs

    @staticmethod
    def _walk_forward_select(
        bars: list[PriceBar],
        horizon_bars: int,
        configs: list[tuple[str, dict[str, Any]]],
    ) -> dict[str, float]:
        """Mean validation Brier per config across sequential pre-tail folds.

        Each fold trains on a prefix of the bars; the trainer's own trailing
        test slice inside that prefix is the fold's validation window. Both
        folds end before the final gate tail (the last 20% of the full
        series), so selection never touches the data the gate will use.
        """
        n = len(bars)
        scores: dict[str, float] = {}
        for name, kwargs in configs:
            fold_briers: list[float] = []
            for frac in _SELECTION_FOLDS:
                prefix = bars[: int(n * frac)]
                if len(prefix) < 300:
                    continue
                try:
                    model = train_sklearn_forecaster(
                        bars=prefix,
                        horizon_bars=horizon_bars,
                        compute_importances=False,
                        **kwargs,
                    )
                except ValidationError as exc:
                    log.warning("promotion.fold_skipped", config=name, error=str(exc))
                    continue
                fold_briers.append(model.report.effective_brier)
            if fold_briers:
                scores[name] = sum(fold_briers) / len(fold_briers)
        return scores

    # ---- champion re-grade + demotion --------------------------------------

    def _regrade_champion(
        self,
        champion: dict[str, object],
        *,
        bars: list[PriceBar],
        horizon_bars: int,
        news_by_ts: Mapping[datetime, Mapping[str, float]] | None,
        macro_by_ts: Mapping[datetime, Mapping[str, float]] | None,
        htf_by_ts: Mapping[datetime, Mapping[str, float]] | None = None,
    ) -> float | None:
        """Champion Brier on the same fresh tail the challengers used.

        Graded under the champion's own abstention margin, so incumbent and
        challenger are both judged on the hours they each choose to act on.
        """
        name = str(champion.get("model_name") or "")
        if not name:
            return None
        try:
            model, _ = self._store.load(name)
        except (ValidationError, OSError, ValueError, KeyError) as exc:
            log.warning("promotion.champion_regrade_failed", name=name, error=str(exc))
            return None
        policy = evaluate_policy_on_tail(
            model,
            bars=bars,
            horizon_bars=horizon_bars,
            news_by_ts=news_by_ts,
            macro_by_ts=macro_by_ts,
        )
        if policy is None:
            return None
        # A champion whose margin has stopped clearing anything is not
        # meaningfully predicting; grade it on every hour instead.
        return policy.brier_covered if policy.n_covered > 0 else policy.brier_all

    def _update_floor_streak(
        self, champion: dict[str, object], champion_fresh: float | None
    ) -> tuple[int, bool]:
        """Advance the incumbent's floor-failure streak; True = demote now.

        Only a *measured* fresh re-grade moves the streak — when re-grading
        was impossible we neither punish nor forgive.
        """
        raw_streak = champion.get("floor_failures")
        streak = int(raw_streak) if isinstance(raw_streak, (int, float)) else 0
        if champion_fresh is None:
            return streak, False
        streak = streak + 1 if champion_fresh > _BASELINE_FLOOR else 0
        raw_brier = champion.get("test_brier")
        self._write_champion(
            name=str(champion.get("model_name")),
            brier=float(raw_brier) if isinstance(raw_brier, (int, float)) else 0.0,
            family=str(champion.get("feature_family") or "unknown"),
            floor_failures=streak,
        )
        return streak, streak >= _DEMOTION_AFTER

    def _demote_champion(self) -> None:
        self._champion_path.unlink(missing_ok=True)

    # ---- first-champion decision -------------------------------------------

    def _decide_first_champion(
        self,
        *,
        challenger_name: str,
        challenger_brier: float,
        family: str,
        candidate_briers: dict[str, float],
        beats_floor: bool,
        floor_detail: str = "",
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
            blocked_by = floor_detail or (
                f" Its Brier {challenger_brier:.4f} does not beat the coin-flip floor "
                f"{_BASELINE_FLOOR:.3f}."
            )
            reason = (
                f"Challenger ({family}) does not clear the promotion floors — no champion "
                f"installed; the transparent baseline rule keeps predicting.{blocked_by}"
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

    # ---- the retrain ---------------------------------------------------------

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

        news_by_ts, macro_by_ts, htf_by_ts = await self._exogenous_context(bars, symbol)
        configs = self._candidate_configs(news_by_ts, macro_by_ts, htf_by_ts)

        # Walk-forward selection over pre-tail folds, then one final training
        # of the winner on the full series. All CPU-heavy work runs in worker
        # threads so the single-process API stays responsive.
        selection = await asyncio.to_thread(
            self._walk_forward_select, bars, horizon_bars, configs
        )
        if not selection:
            raise ValidationError("no candidate configuration produced a valid fold score")
        family = min(selection, key=lambda k: selection[k])
        winner_kwargs = dict(configs)[family]
        log.info("promotion.selection", folds=selection, winner=family)

        challenger = await asyncio.to_thread(
            train_sklearn_forecaster,
            bars=bars,
            horizon_bars=horizon_bars,
            **winner_kwargs,
        )
        challenger_brier = challenger.report.effective_brier
        candidate_briers = dict(selection)
        candidate_briers[f"{family} (final)"] = challenger_brier

        # Persist only the winning challenger — losers stay out of the store.
        stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        challenger_name = f"auto_{symbol.lower()}_{timeframe.value}_{stamp}"
        self._store.save(
            challenger, name=challenger_name, symbol=symbol, timeframe=timeframe.value
        )

        r = challenger.report
        economics = estimate_breakeven(
            [float(b.close) for b in bars],
            horizon_bars=horizon_bars,
            cost_per_trade_price=round_trip_cost_price(symbol),
        )
        beats_floor, floor_detail = clears_floors(
            r, brier=challenger_brier, economics=economics
        )

        champion = self.current_champion()
        if champion is None:
            first = self._decide_first_champion(
                challenger_name=challenger_name,
                challenger_brier=challenger_brier,
                family=family,
                candidate_briers=candidate_briers,
                beats_floor=beats_floor,
                floor_detail=floor_detail,
            )
            first = replace(
                first,
                breakeven=economics.breakeven,
                challenger_accuracy=r.effective_accuracy,
            )
            self._log_decision(first)
            await self._log_lesson(first, challenger, selection)
            return first

        # Fair gate: champion re-graded on the same fresh window when possible.
        champion_fresh = await asyncio.to_thread(
            self._regrade_champion,
            champion,
            bars=bars,
            horizon_bars=horizon_bars,
            news_by_ts=news_by_ts,
            macro_by_ts=macro_by_ts,
        )
        decision = replace(
            self._decide_vs_incumbent(
                champion=champion,
                champion_fresh=champion_fresh,
                challenger_name=challenger_name,
                challenger_brier=challenger_brier,
                family=family,
                candidate_briers=candidate_briers,
                beats_floor=beats_floor,
                floor_detail=floor_detail,
            ),
            breakeven=economics.breakeven,
            challenger_accuracy=r.effective_accuracy,
        )
        self._log_decision(decision)
        await self._log_lesson(decision, challenger, selection)
        return decision

    def _decide_vs_incumbent(
        self,
        *,
        champion: dict[str, object],
        champion_fresh: float | None,
        challenger_name: str,
        challenger_brier: float,
        family: str,
        candidate_briers: dict[str, float],
        beats_floor: bool,
        floor_detail: str = "",
    ) -> PromotionResult:
        """Gate the challenger against the incumbent; handle demotion."""
        raw_stored = champion.get("test_brier")
        champion_stored = float(raw_stored) if isinstance(raw_stored, (int, float)) else 0.25
        champion_brier = champion_fresh if champion_fresh is not None else champion_stored
        basis = "re-graded on the same fresh window" if champion_fresh is not None else "stored"

        improvement = champion_brier - challenger_brier
        demoted = False
        if improvement >= _PROMOTION_MARGIN and beats_floor:
            self._write_champion(name=challenger_name, brier=challenger_brier, family=family)
            promoted = True
            reason = (
                f"Challenger ({family}) Brier {challenger_brier:.4f} beat champion "
                f"{champion_brier:.4f} ({basis}) by {improvement:.4f} "
                f"(≥ {_PROMOTION_MARGIN}) and clears the coin-flip floor — promoted."
            )
        else:
            promoted = False
            if improvement >= _PROMOTION_MARGIN:
                # Name the floor that actually blocked it. "Failed the gate" with
                # three gates behind it tells the reader nothing about what to fix.
                blocked_by = floor_detail or (
                    f" Its Brier {challenger_brier:.4f} does not clear the coin-flip "
                    f"floor {_BASELINE_FLOOR:.3f}."
                )
                reason = (
                    f"Challenger ({family}) Brier {challenger_brier:.4f} beat the champion "
                    f"{champion_brier:.4f} ({basis}) but does not clear the promotion "
                    f"floors — not promoted. Beating a bad incumbent is not the same as "
                    f"being good.{blocked_by}"
                )
            else:
                reason = (
                    f"Challenger ({family}) Brier {challenger_brier:.4f} did not beat champion "
                    f"{champion_brier:.4f} ({basis}) by the required {_PROMOTION_MARGIN} "
                    f"margin — champion kept. A worse model never ships."
                )
            # The incumbent survived the challenge — but does it still deserve
            # the crown? Track fresh-window floor failures with hysteresis.
            streak, demote_now = self._update_floor_streak(champion, champion_fresh)
            if demote_now:
                self._demote_champion()
                demoted = True
                reason += (
                    f" Incumbent's fresh re-grade failed the coin-flip floor "
                    f"{streak} retrains in a row — demoted. The transparent baseline "
                    f"rule predicts until a challenger genuinely earns the crown."
                )
                log.warning(
                    "promotion.champion_demoted",
                    champion=champion.get("model_name"),
                    streak=streak,
                )
            elif champion_fresh is not None and champion_fresh > _BASELINE_FLOOR:
                reason += f" (Incumbent floor-failure streak: {streak}/{_DEMOTION_AFTER}.)"

        log.info(
            "promotion.decision",
            promoted=promoted,
            demoted=demoted,
            challenger=challenger_name,
            challenger_family=family,
            challenger_brier=challenger_brier,
            champion=champion.get("model_name"),
            champion_brier=champion_brier,
            champion_brier_basis=basis,
        )
        return PromotionResult(
            challenger_name=challenger_name,
            challenger_brier=challenger_brier,
            champion_name=str(champion.get("model_name")),
            champion_brier=champion_brier,
            promoted=promoted,
            reason=reason,
            challenger_family=family,
            candidate_briers=candidate_briers,
            champion_brier_fresh=champion_fresh,
            demoted=demoted,
        )
