"""Scikit-learn–backed gradient-boosting forecaster.

We use `HistGradientBoostingClassifier` — sklearn's native gradient-
boosted decision trees. It performs comparably to LightGBM/XGBoost on
small tabular problems while avoiding their compilation footprint and
keeping installs simple.

Outputs `predict_proba` → `p_up`. The forecast object is built by the
shared base class so the application layer sees the same `Forecaster`
contract whether the brain is a rule, a tree, or (later) something
ensembled.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss

from mentor.domain.errors import ValidationError
from mentor.domain.forecasting.features import (
    FEATURE_NAMES,
    build_feature_row,
    build_feature_series,
)
from mentor.domain.forecasting.forecast import (
    Forecast,
    direction_from_probability,
)
from mentor.domain.forecasting.forecaster import Forecaster
from mentor.domain.forecasting.labels import build_labels
from mentor.domain.forecasting.regime import (
    FeatureDistribution,
    build_feature_distribution,
)
from mentor.domain.market.bars import PriceBar, Timeframe


@dataclass(frozen=True, slots=True)
class TrainingReport:
    n_samples: int
    n_train: int
    n_test: int
    train_accuracy: float
    test_accuracy: float
    test_log_loss: float
    test_brier: float
    horizon_bars: int
    feature_importances: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class SklearnForecaster(Forecaster):
    """Trained ML forecaster. Wraps a fitted sklearn classifier."""

    _classifier: HistGradientBoostingClassifier
    _horizon_bars: int
    _report: TrainingReport
    _distribution: FeatureDistribution | None = None

    @property
    def name(self) -> str:
        return f"sklearn_hgb(h={self._horizon_bars})"

    @property
    def horizon_bars(self) -> int:
        return self._horizon_bars

    @property
    def report(self) -> TrainingReport:
        return self._report

    @property
    def distribution(self) -> FeatureDistribution | None:
        return self._distribution

    def forecast(
        self,
        *,
        bars: Sequence[PriceBar],
        symbol: str,
        timeframe: Timeframe,
    ) -> Forecast:
        row = build_feature_row(bars)
        if row is None:
            raise ValidationError("not enough history to build features")

        x = np.array([[float(row.features[name]) for name in FEATURE_NAMES]])
        proba = self._classifier.predict_proba(x)[0]
        p_up = Decimal(str(round(float(proba[1]), 4)))
        confidence = abs(p_up - Decimal("0.5")) * Decimal("2")
        direction = direction_from_probability(p_up)

        # Top contributing features (by training importance), with the
        # current values — that becomes the "why" the LLM synthesizes on.
        importance_pairs = sorted(
            self._report.feature_importances.items(), key=lambda kv: kv[1], reverse=True
        )[:3]
        top_features = ", ".join(
            f"{name}={float(row.features[name]):+.4f}" for name, _ in importance_pairs
        )

        reasoning = (
            f"ML lean {p_up * 100:.0f}% probability up over the next "
            f"{self._horizon_bars} bars (confidence {confidence * 100:.0f}%). "
            f"Top drivers: {top_features or 'n/a'}. This is a tree model — "
            f"the read can flip quickly if those features change."
        )

        return Forecast(
            symbol=symbol.upper(),
            timeframe=timeframe,
            asof=bars[-1].ts,
            asof_close=bars[-1].close,
            horizon_bars=self._horizon_bars,
            p_up=p_up,
            confidence=confidence,
            direction=direction,
            model_name=self.name,
            reasoning=reasoning,
            features=row.features,
        )


def train_sklearn_forecaster(
    *,
    bars: Sequence[PriceBar],
    horizon_bars: int,
    test_fraction: float = 0.2,
    classifier_params: dict[str, Any] | None = None,
    seed: int = 42,
) -> SklearnForecaster:
    """Train on `bars`, holding out a *trailing* fraction as test.

    Held-out test is at the end of the series (no random shuffle) — that
    mirrors live use and exposes regime drift the way the plan's
    walk-forward methodology does.
    """
    if len(bars) < 250:
        raise ValidationError(f"need at least 250 bars to train; got {len(bars)}")
    rows = build_feature_series(bars)
    if len(rows) < 100:
        raise ValidationError(f"only {len(rows)} feature rows — not enough to train")

    closes = [b.close for b in bars]
    timestamps = [b.ts for b in bars]
    label_by_ts: dict[datetime, int] = {
        ts: y for ts, y in build_labels(closes, timestamps=timestamps, horizon_bars=horizon_bars)
    }

    samples: list[tuple[list[float], int]] = []
    for row in rows:
        if row.ts not in label_by_ts:
            continue  # tail rows have no label (horizon not elapsed)
        samples.append(
            (
                [float(row.features[name]) for name in FEATURE_NAMES],
                label_by_ts[row.ts],
            )
        )

    if len(samples) < 100:
        raise ValidationError(f"only {len(samples)} usable samples after labelling")

    split = int(len(samples) * (1 - test_fraction))
    if split < 50 or split >= len(samples):
        raise ValidationError("not enough samples to honour train/test split")

    train_x = np.array([s[0] for s in samples[:split]])
    train_y = np.array([s[1] for s in samples[:split]])
    test_x = np.array([s[0] for s in samples[split:]])
    test_y = np.array([s[1] for s in samples[split:]])

    params = {
        "learning_rate": 0.05,
        "max_depth": 4,
        "max_iter": 200,
        "min_samples_leaf": 25,
        "l2_regularization": 1.0,
        "random_state": seed,
    }
    params.update(classifier_params or {})

    clf = HistGradientBoostingClassifier(**params)
    clf.fit(train_x, train_y)

    train_acc = float(accuracy_score(train_y, clf.predict(train_x)))
    test_pred = clf.predict(test_x)
    test_proba = clf.predict_proba(test_x)[:, 1]
    test_acc = float(accuracy_score(test_y, test_pred))
    test_ll = float(log_loss(test_y, np.clip(test_proba, 1e-6, 1 - 1e-6)))
    test_brier = float(brier_score_loss(test_y, test_proba))

    # Permutation importance is heavy on this scale; we approximate
    # importance using the gradient norm proxy via gain-based feature
    # importance from sklearn's tree mixin when available.
    importances: dict[str, float] = {}
    try:
        gain = clf.feature_importances_
        importances = {name: float(value) for name, value in zip(FEATURE_NAMES, gain, strict=True)}
    except AttributeError:  # sklearn version without the attr
        importances = {name: 0.0 for name in FEATURE_NAMES}

    report = TrainingReport(
        n_samples=len(samples),
        n_train=split,
        n_test=len(samples) - split,
        train_accuracy=train_acc,
        test_accuracy=test_acc,
        test_log_loss=test_ll,
        test_brier=test_brier,
        horizon_bars=horizon_bars,
        feature_importances=importances,
    )

    # Capture the empirical p5/p95 envelope of every feature seen during
    # training so inference can flag out-of-regime conditions later.
    train_rows = rows[:split] if split <= len(rows) else rows
    distribution = build_feature_distribution(train_rows) if train_rows else None

    return SklearnForecaster(
        _classifier=clf,
        _horizon_bars=horizon_bars,
        _report=report,
        _distribution=distribution,
    )
