"""Scikit-learn gradient-boosting **volatility** regressor.

Mirrors ``sklearn_forecaster.py`` (the direction classifier) but predicts a
continuous target — the future realized volatility ``future_rv[t] =
stdev(log_returns[t+1 .. t+H])`` — with ``HistGradientBoostingRegressor``.

The training report is *honest by construction*: it evaluates the model on
a trailing hold-out against the RiskMetrics **EWMA baseline** using proper
volatility losses (MAE, QLIKE) plus an out-of-sample R^2 *relative to EWMA*.
``beats_ewma`` is true only if the ML model actually reduces error out of
sample — the same champion/challenger discipline as the direction side. If
it doesn't beat EWMA, callers keep EWMA and say so.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance

from mentor.domain.errors import ValidationError
from mentor.domain.forecasting.macro_features import MACRO_FEATURE_NAMES
from mentor.domain.forecasting.vol_features import (
    VOL_FEATURE_NAMES,
    build_vol_feature_row,
    build_vol_feature_series,
)
from mentor.domain.forecasting.volatility import (
    VolForecast,
    VolForecaster,
    build_vol_forecast,
    ewma_vol,
    log_returns,
    realized_vol,
    rolling_realized_vol,
)
from mentor.domain.market.bars import PriceBar, Timeframe

# A tiny variance floor so QLIKE and pip-range math never divide by zero on a
# dead-flat window.
_VOL_FLOOR = 1e-9


@dataclass(frozen=True, slots=True)
class VolTrainingReport:
    n_samples: int
    n_train: int
    n_test: int
    horizon_bars: int
    ml_mae: float
    ewma_mae: float
    ml_qlike: float
    ewma_qlike: float
    ml_r2: float  # standard R^2 of ML vs the actual future vol
    r2_vs_ewma: float  # 1 - SSE_ml/SSE_ewma; > 0 means ML beats EWMA out-of-sample
    beats_ewma: bool
    conformal_q90: float = 0.0  # 90th pct of |residual| on test — the coverage band
    feature_importances: dict[str, float] = field(default_factory=dict)

    @property
    def verdict(self) -> str:
        if self.beats_ewma:
            return (
                f"ML beats EWMA out-of-sample: MAE {self.ml_mae:.2e} vs {self.ewma_mae:.2e}, "
                f"QLIKE {self.ml_qlike:.4f} vs {self.ewma_qlike:.4f} "
                f"(R2 vs EWMA {self.r2_vs_ewma:+.3f}). Ship the ML vol model."
            )
        return (
            f"ML does NOT beat EWMA out-of-sample (MAE {self.ml_mae:.2e} vs {self.ewma_mae:.2e}, "
            f"QLIKE {self.ml_qlike:.4f} vs {self.ewma_qlike:.4f}, R2 vs EWMA "
            f"{self.r2_vs_ewma:+.3f}). Keep the transparent EWMA baseline."
        )


@dataclass(slots=True)
class SklearnVolForecaster(VolForecaster):
    """Trained ML vol regressor. Predicts per-bar realized vol, then reuses
    the shared range/percentile/regime presentation."""

    _regressor: HistGradientBoostingRegressor
    _horizon_bars: int
    _report: VolTrainingReport
    _conformal_q90: float = 0.0
    _feature_names: tuple[str, ...] = VOL_FEATURE_NAMES
    _macro_feature_names: tuple[str, ...] = ()

    @property
    def feature_names(self) -> tuple[str, ...]:
        # getattr guard: old pickles predate this slot -> technical-only.
        return getattr(self, "_feature_names", None) or VOL_FEATURE_NAMES

    @property
    def macro_feature_names(self) -> tuple[str, ...]:
        return getattr(self, "_macro_feature_names", None) or ()

    @property
    def uses_macro(self) -> bool:
        return bool(self.macro_feature_names)

    @property
    def name(self) -> str:
        suffix = ",macro" if self.uses_macro else ""
        return f"sklearn_vol_hgb(h={self._horizon_bars}{suffix})"

    @property
    def horizon_bars(self) -> int:
        return self._horizon_bars

    @property
    def report(self) -> VolTrainingReport:
        return self._report

    def forecast_vol(
        self,
        *,
        bars: Sequence[PriceBar],
        symbol: str,
        timeframe: Timeframe,
        horizon_bars: int,
        pip_size: Decimal,
        macro: Mapping[str, float] | None = None,
    ) -> VolForecast:
        row = build_vol_feature_row(bars)
        if row is None:
            raise ValidationError("not enough history for a volatility read", field="bars")
        combined: dict[str, float] = {k: float(v) for k, v in row.features.items()}
        for mf in self.macro_feature_names:
            combined[mf] = float((macro or {}).get(mf, 0.0))
        x = np.array([[combined.get(name, 0.0) for name in self.feature_names]])
        pred = float(self._regressor.predict(x)[0])
        per_bar = Decimal(str(max(pred, 0.0)))
        history = rolling_realized_vol([b.close for b in bars])
        q90 = getattr(self, "_conformal_q90", 0.0)
        conformal_q = Decimal(str(q90)) if q90 > 0 else None
        return build_vol_forecast(
            symbol=symbol,
            timeframe=timeframe,
            asof=bars[-1].ts,
            asof_close=bars[-1].close,
            horizon_bars=horizon_bars,
            per_bar_vol=per_bar,
            history=history,
            pip_size=pip_size,
            model_name=self.name,
            conformal_q=conformal_q,
            coverage=Decimal("0.90"),
        )


def _future_rv_labels(closes: Sequence[Decimal], horizon_bars: int) -> dict[int, float]:
    """future_rv[i] = stdev(log_returns over bars i..i+H). Keyed by bar index.

    Point-in-time: the label at bar ``i`` uses only returns *after* ``i``.
    """
    rets = log_returns(closes)  # rets[k] is the return from bar k to bar k+1
    labels: dict[int, float] = {}
    for i in range(len(rets) - horizon_bars + 1):
        window = rets[i : i + horizon_bars]
        rv = realized_vol(window)
        if rv is not None:
            labels[i] = float(rv)
    return labels


def _qlike(actual_vol: float, pred_vol: float) -> float:
    """QLIKE loss on variances — a proper scoring rule for volatility."""
    a = max(actual_vol, _VOL_FLOOR) ** 2
    p = max(pred_vol, _VOL_FLOOR) ** 2
    return a / p - math.log(a / p) - 1.0


def _vol_permutation_importance(
    reg: HistGradientBoostingRegressor,
    x_test: Any,
    y_test: Any,
    *,
    feature_names: tuple[str, ...],
    seed: int,
) -> dict[str, float]:
    importances: dict[str, float] = dict.fromkeys(feature_names, 0.0)
    try:
        pi = permutation_importance(reg, x_test, y_test, n_repeats=5, random_state=seed)
        importances = {
            name: float(val)
            for name, val in zip(feature_names, pi.importances_mean, strict=True)
        }
    except ValueError:  # pragma: no cover - defensive
        pass
    return importances


def _build_vol_samples(
    bars: Sequence[PriceBar],
    horizon_bars: int,
    macro_by_ts: Mapping[datetime, Mapping[str, float]] | None,
) -> tuple[tuple[str, ...], tuple[str, ...], list[list[float]], list[float], list[float]]:
    """Feature names + per-sample (vector, actual future vol, EWMA forecast)."""
    rows = build_vol_feature_series(bars)
    if len(rows) < 100:
        raise ValidationError(f"only {len(rows)} vol feature rows — too few to train", field="bars")
    closes = [b.close for b in bars]
    ts_to_index = {b.ts: i for i, b in enumerate(bars)}
    rets = log_returns(closes)
    labels_by_index = _future_rv_labels(closes, horizon_bars)

    use_macro = macro_by_ts is not None
    macro_names: tuple[str, ...] = MACRO_FEATURE_NAMES if use_macro else ()
    feature_names: tuple[str, ...] = VOL_FEATURE_NAMES + macro_names

    vectors: list[list[float]] = []
    actuals: list[float] = []
    ewma_preds: list[float] = []
    for row in rows:
        idx = ts_to_index.get(row.ts)
        if idx is None or idx not in labels_by_index:
            continue
        vector = [float(row.features[name]) for name in VOL_FEATURE_NAMES]
        if use_macro:
            assert macro_by_ts is not None
            macro_row = macro_by_ts.get(row.ts, {})
            vector.extend(float(macro_row.get(name, 0.0)) for name in macro_names)
        vectors.append(vector)
        actuals.append(labels_by_index[idx])
        ewma = ewma_vol(rets[:idx])  # returns strictly up to bar idx
        ewma_preds.append(float(ewma) if ewma is not None else 0.0)
    return feature_names, macro_names, vectors, actuals, ewma_preds


def train_sklearn_vol_forecaster(
    *,
    bars: Sequence[PriceBar],
    horizon_bars: int,
    test_fraction: float = 0.2,
    seed: int = 42,
    macro_by_ts: Mapping[datetime, Mapping[str, float]] | None = None,
) -> SklearnVolForecaster:
    """Train the vol regressor on a trailing hold-out and grade it vs EWMA.

    The hold-out is the *end* of the series (no shuffle) — walk-forward-ish,
    exposing regime drift the same way the direction trainer does.

    If ``macro_by_ts`` is supplied, each sample's vector is extended with the
    FX-driver features (rates, DXY, VIX) aligned to that bar — VIX especially
    is a plausible predictor of realized vol. Whether it actually helps is
    decided by the same honest MAE/QLIKE-vs-EWMA gate.
    """
    if len(bars) < 250:
        raise ValidationError(f"need at least 250 bars to train vol; got {len(bars)}", field="bars")
    feature_names, macro_names, vectors, actuals, ewma_preds = _build_vol_samples(
        bars, horizon_bars, macro_by_ts
    )
    if len(vectors) < 100:
        raise ValidationError(f"only {len(vectors)} usable vol samples labelled", field="bars")

    split = int(len(vectors) * (1 - test_fraction))
    if split < 50 or split >= len(vectors):
        raise ValidationError("not enough samples to honour vol train/test split", field="bars")

    x_train = np.array(vectors[:split])
    y_train = np.array(actuals[:split])
    x_test = np.array(vectors[split:])
    y_test = np.array(actuals[split:])
    ewma_test = np.array(ewma_preds[split:])

    reg = HistGradientBoostingRegressor(
        learning_rate=0.05,
        max_depth=3,
        max_iter=300,
        min_samples_leaf=30,
        l2_regularization=1.0,
        loss="squared_error",
        random_state=seed,
    )
    reg.fit(x_train, y_train)

    ml_test = np.clip(reg.predict(x_test), 0.0, None)

    # Split-conformal: 90th percentile of |residual| on the held-out test is
    # the +/- band that (empirically) covers ~90% of forecast errors.
    conformal_q90 = float(np.quantile(np.abs(ml_test - y_test), 0.90))

    ml_mae = float(np.mean(np.abs(ml_test - y_test)))
    ewma_mae = float(np.mean(np.abs(ewma_test - y_test)))
    ml_qlike = float(np.mean([_qlike(a, p) for a, p in zip(y_test, ml_test, strict=True)]))
    ewma_qlike = float(np.mean([_qlike(a, p) for a, p in zip(y_test, ewma_test, strict=True)]))

    sse_ml = float(np.sum((y_test - ml_test) ** 2))
    sse_ewma = float(np.sum((y_test - ewma_test) ** 2))
    sst = float(np.sum((y_test - float(np.mean(y_test))) ** 2))
    ml_r2 = 1.0 - sse_ml / sst if sst > 0 else 0.0
    r2_vs_ewma = 1.0 - sse_ml / sse_ewma if sse_ewma > 0 else 0.0
    # Honest gate: ML must reduce BOTH squared error and QLIKE vs EWMA.
    beats_ewma = sse_ml < sse_ewma and ml_qlike < ewma_qlike

    importances = _vol_permutation_importance(
        reg, x_test, y_test, feature_names=feature_names, seed=seed
    )

    report = VolTrainingReport(
        n_samples=len(vectors),
        n_train=split,
        n_test=len(vectors) - split,
        horizon_bars=horizon_bars,
        ml_mae=ml_mae,
        ewma_mae=ewma_mae,
        ml_qlike=ml_qlike,
        ewma_qlike=ewma_qlike,
        ml_r2=ml_r2,
        r2_vs_ewma=r2_vs_ewma,
        beats_ewma=beats_ewma,
        conformal_q90=conformal_q90,
        feature_importances=importances,
    )
    return SklearnVolForecaster(
        _regressor=reg,
        _horizon_bars=horizon_bars,
        _report=report,
        _conformal_q90=conformal_q90,
        _feature_names=feature_names,
        _macro_feature_names=macro_names,
    )
