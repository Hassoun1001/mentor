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

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss

from mentor.domain.errors import ValidationError
from mentor.domain.forecasting.calibration import expected_calibration_error
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
from mentor.domain.forecasting.macro_features import MACRO_FEATURE_NAMES
from mentor.domain.forecasting.news_features import NEWS_FEATURE_NAMES
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
    # Calibration (added later; defaults keep old metadata JSON parseable).
    n_calibration: int = 0
    test_brier_uncalibrated: float = 0.0
    ece: float = 0.0  # of the *shipped* probabilities (calibrated if applied)
    ece_uncalibrated: float = 0.0
    calibration_applied: bool = False


@dataclass(slots=True)
class SklearnForecaster(Forecaster):
    """Trained ML forecaster. Wraps a fitted sklearn classifier.

    A model carries its own ordered ``_feature_names`` so a news-aware
    model (technical + news columns) and a technical-only model share one
    class. ``_news_feature_names`` is the subset that must be supplied via
    the ``news`` argument at forecast time. Both fields default so models
    pickled before they existed still load as technical-only.
    """

    _classifier: HistGradientBoostingClassifier
    _horizon_bars: int
    _report: TrainingReport
    _distribution: FeatureDistribution | None = None
    _feature_names: tuple[str, ...] = FEATURE_NAMES
    _news_feature_names: tuple[str, ...] = ()
    _macro_feature_names: tuple[str, ...] = ()
    _calibrator: IsotonicRegression | None = None

    @property
    def feature_names(self) -> tuple[str, ...]:
        # getattr guard: old pickles predate this slot → technical-only.
        return getattr(self, "_feature_names", None) or FEATURE_NAMES

    @property
    def news_feature_names(self) -> tuple[str, ...]:
        return getattr(self, "_news_feature_names", None) or ()

    @property
    def macro_feature_names(self) -> tuple[str, ...]:
        return getattr(self, "_macro_feature_names", None) or ()

    @property
    def uses_news(self) -> bool:
        return bool(self.news_feature_names)

    @property
    def uses_macro(self) -> bool:
        return bool(self.macro_feature_names)

    @property
    def calibrator(self) -> IsotonicRegression | None:
        # getattr guard: old pickles predate this slot → uncalibrated.
        return getattr(self, "_calibrator", None)

    @property
    def name(self) -> str:
        suffix = ",news" if self.uses_news else ""
        suffix += ",macro" if self.uses_macro else ""
        return f"sklearn_hgb(h={self._horizon_bars}{suffix})"

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
        news: Mapping[str, float] | None = None,
        macro: Mapping[str, float] | None = None,
    ) -> Forecast:
        row = build_feature_row(bars)
        if row is None:
            raise ValidationError("not enough history to build features")

        # Combined feature pool: technical (Decimal) + news + macro (float).
        # Missing exogenous columns default to neutral 0.0 — same as "no signal".
        combined: dict[str, float] = {k: float(v) for k, v in row.features.items()}
        for nf in self.news_feature_names:
            combined[nf] = float((news or {}).get(nf, 0.0))
        for mf in self.macro_feature_names:
            combined[mf] = float((macro or {}).get(mf, 0.0))

        x = np.array([[combined.get(name, 0.0) for name in self.feature_names]])
        proba = self._classifier.predict_proba(x)[0]
        raw_p = float(proba[1])
        # Apply the isotonic calibrator when one was fitted and shipped, so
        # the displayed probability matches the realised hit rate.
        calibrator = self.calibrator
        shipped_p = float(calibrator.predict([raw_p])[0]) if calibrator is not None else raw_p
        shipped_p = min(1.0, max(0.0, shipped_p))
        p_up = Decimal(str(round(shipped_p, 4)))
        confidence = abs(p_up - Decimal("0.5")) * Decimal("2")
        direction = direction_from_probability(p_up)

        # Top contributing features (by training importance), with the
        # current values — that becomes the "why" the LLM synthesizes on.
        importance_pairs = sorted(
            self._report.feature_importances.items(), key=lambda kv: kv[1], reverse=True
        )[:3]
        top_features = ", ".join(
            f"{name}={combined.get(name, 0.0):+.4f}" for name, _ in importance_pairs
        )

        news_note = ""
        if self.uses_news:
            tone = combined.get("news_tone_5d", 0.0)
            mood = "negative" if tone < -0.05 else "positive" if tone > 0.05 else "neutral"
            news_note = f" News mood is {mood} (5d tone {tone:+.2f})."

        reasoning = (
            f"ML lean {p_up * 100:.0f}% probability up over the next "
            f"{self._horizon_bars} bars (confidence {confidence * 100:.0f}%). "
            f"Top drivers: {top_features or 'n/a'}.{news_note} This is a tree model — "
            f"the read can flip quickly if those features change."
        )

        # Audit snapshot includes the exogenous columns the model used.
        features_snapshot = dict(row.features)
        for nf in self.news_feature_names:
            features_snapshot[nf] = Decimal(str(round(combined.get(nf, 0.0), 6)))
        for mf in self.macro_feature_names:
            features_snapshot[mf] = Decimal(str(round(combined.get(mf, 0.0), 6)))

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
            features=features_snapshot,
        )


def _assemble_samples(
    rows: Sequence[Any],
    *,
    bars: Sequence[PriceBar],
    horizon_bars: int,
    news_by_ts: Mapping[datetime, Mapping[str, float]] | None,
    macro_by_ts: Mapping[datetime, Mapping[str, float]] | None,
) -> tuple[list[tuple[list[float], int]], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Build labelled feature vectors (technical + optional news + macro).

    Returns the samples plus the ordered ``feature_names`` and the news/macro
    name subsets so the trainer records exactly which columns the model needs
    at inference time.
    """
    closes = [b.close for b in bars]
    timestamps = [b.ts for b in bars]
    label_by_ts: dict[datetime, int] = {
        ts: y for ts, y in build_labels(closes, timestamps=timestamps, horizon_bars=horizon_bars)
    }

    news_names: tuple[str, ...] = NEWS_FEATURE_NAMES if news_by_ts is not None else ()
    macro_names: tuple[str, ...] = MACRO_FEATURE_NAMES if macro_by_ts is not None else ()
    feature_names: tuple[str, ...] = FEATURE_NAMES + news_names + macro_names

    samples: list[tuple[list[float], int]] = []
    for row in rows:
        if row.ts not in label_by_ts:
            continue  # tail rows have no label (horizon not elapsed)
        vector = [float(row.features[name]) for name in FEATURE_NAMES]
        if news_by_ts is not None:
            news_row = news_by_ts.get(row.ts, {})
            vector.extend(float(news_row.get(name, 0.0)) for name in news_names)
        if macro_by_ts is not None:
            macro_row = macro_by_ts.get(row.ts, {})
            vector.extend(float(macro_row.get(name, 0.0)) for name in macro_names)
        samples.append((vector, label_by_ts[row.ts]))
    return samples, feature_names, news_names, macro_names


def evaluate_forecaster_on_tail(
    forecaster: SklearnForecaster,
    *,
    bars: Sequence[PriceBar],
    horizon_bars: int,
    test_fraction: float = 0.2,
    news_by_ts: Mapping[datetime, Mapping[str, float]] | None = None,
    macro_by_ts: Mapping[datetime, Mapping[str, float]] | None = None,
) -> float | None:
    """Grade an already-trained forecaster on the trailing test slice of `bars`.

    This is what makes champion/challenger promotion *fair*: the champion's
    stored Brier was measured on the data of its own era, while a fresh
    challenger is graded on today's tail. Re-grading both on the **same**
    trailing window compares like with like. Feature vectors are assembled in
    the forecaster's own column order (technical-only and news/macro-aware
    models both work); missing exogenous columns default to neutral 0.0,
    exactly as at inference time.

    Returns the Brier score of the shipped (calibrated when the model carries
    a calibrator) probabilities, or ``None`` when the tail is too small to
    grade meaningfully.
    """
    rows = build_feature_series(bars)
    closes = [b.close for b in bars]
    timestamps = [b.ts for b in bars]
    label_by_ts: dict[datetime, int] = {
        ts: y for ts, y in build_labels(closes, timestamps=timestamps, horizon_bars=horizon_bars)
    }

    samples: list[tuple[list[float], int]] = []
    for row in rows:
        if row.ts not in label_by_ts:
            continue
        combined: dict[str, float] = {k: float(v) for k, v in row.features.items()}
        if news_by_ts is not None:
            combined.update(news_by_ts.get(row.ts, {}))
        if macro_by_ts is not None:
            combined.update(macro_by_ts.get(row.ts, {}))
        vector = [combined.get(name, 0.0) for name in forecaster.feature_names]
        samples.append((vector, label_by_ts[row.ts]))

    if len(samples) < 100:
        return None
    test_split = int(len(samples) * (1 - test_fraction))
    tail = samples[test_split:]
    if len(tail) < 20:
        return None

    x = np.array([s[0] for s in tail])
    y = np.array([s[1] for s in tail])
    raw = forecaster._classifier.predict_proba(x)[:, 1]
    calibrator = forecaster.calibrator
    shipped = np.clip(calibrator.predict(raw), 0.0, 1.0) if calibrator is not None else raw
    return float(brier_score_loss(y, shipped))


def _fit_and_grade_calibration(
    clf: HistGradientBoostingClassifier,
    *,
    calib_x: Any,
    calib_y: Any,
    test_x: Any,
    test_y: Any,
) -> tuple[IsotonicRegression | None, dict[str, float | bool]]:
    """Fit isotonic calibration on the held-out slice and grade it on test.

    Ship the calibrator only if it *reduces* ECE without worsening Brier on
    the test slice — the same "beat the baseline or keep it simple" honesty
    the champion/challenger gate applies to the model itself. Returns the
    calibrator (or ``None`` if not shipped) plus the shipped-vs-raw metrics.
    """
    raw_test = clf.predict_proba(test_x)[:, 1]
    ece_raw = expected_calibration_error(list(map(float, raw_test)), list(map(int, test_y)))
    brier_raw = float(brier_score_loss(test_y, raw_test))

    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(clf.predict_proba(calib_x)[:, 1], calib_y)
    cal_test = np.clip(iso.predict(raw_test), 0.0, 1.0)
    ece_cal = expected_calibration_error(list(map(float, cal_test)), list(map(int, test_y)))
    brier_cal = float(brier_score_loss(test_y, cal_test))

    applied = ece_cal < ece_raw - 1e-9 and brier_cal <= brier_raw + 1e-9
    shipped = cal_test if applied else raw_test
    metrics: dict[str, float | bool] = {
        "test_accuracy": float(accuracy_score(test_y, (shipped >= 0.5).astype(int))),
        "test_log_loss": float(log_loss(test_y, np.clip(shipped, 1e-6, 1 - 1e-6))),
        "test_brier": float(brier_score_loss(test_y, shipped)),
        "test_brier_uncalibrated": brier_raw,
        "ece": ece_cal if applied else ece_raw,
        "ece_uncalibrated": ece_raw,
        "calibration_applied": applied,
    }
    return (iso if applied else None), metrics


def train_sklearn_forecaster(
    *,
    bars: Sequence[PriceBar],
    horizon_bars: int,
    test_fraction: float = 0.2,
    classifier_params: dict[str, Any] | None = None,
    seed: int = 42,
    news_by_ts: Mapping[datetime, Mapping[str, float]] | None = None,
    macro_by_ts: Mapping[datetime, Mapping[str, float]] | None = None,
) -> SklearnForecaster:
    """Train on `bars`, holding out a *trailing* fraction as test.

    Held-out test is at the end of the series (no random shuffle) — that
    mirrors live use and exposes regime drift the way the plan's
    walk-forward methodology does.

    If `news_by_ts` is supplied, each sample's feature vector is extended
    with the news-sentiment columns aligned to that bar's timestamp
    (missing entries default to neutral 0.0). The returned forecaster
    records that it now requires news at inference time.
    """
    if len(bars) < 250:
        raise ValidationError(f"need at least 250 bars to train; got {len(bars)}")
    rows = build_feature_series(bars)
    if len(rows) < 100:
        raise ValidationError(f"only {len(rows)} feature rows — not enough to train")

    samples, feature_names, news_names, macro_names = _assemble_samples(
        rows,
        bars=bars,
        horizon_bars=horizon_bars,
        news_by_ts=news_by_ts,
        macro_by_ts=macro_by_ts,
    )
    if len(samples) < 100:
        raise ValidationError(f"only {len(samples)} usable samples after labelling")

    # Three-way trailing split: fit | calibration | test. The classifier
    # trains on `fit`, the isotonic calibrator is fitted on `calibration`
    # (which the classifier never saw), and everything is graded on `test`.
    test_split = int(len(samples) * (1 - test_fraction))
    calib_size = max(30, int(test_split * 0.15))
    fit_end = test_split - calib_size
    if fit_end < 50 or test_split >= len(samples):
        raise ValidationError("not enough samples to honour fit/calibration/test split")

    train_x = np.array([s[0] for s in samples[:fit_end]])
    train_y = np.array([s[1] for s in samples[:fit_end]])
    calib_x = np.array([s[0] for s in samples[fit_end:test_split]])
    calib_y = np.array([s[1] for s in samples[fit_end:test_split]])
    test_x = np.array([s[0] for s in samples[test_split:]])
    test_y = np.array([s[1] for s in samples[test_split:]])

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
    calibrator, cal = _fit_and_grade_calibration(
        clf, calib_x=calib_x, calib_y=calib_y, test_x=test_x, test_y=test_y
    )

    # Gain-based feature importance from sklearn's tree mixin when available.
    importances: dict[str, float] = {}
    try:
        gain = clf.feature_importances_
        importances = {name: float(value) for name, value in zip(feature_names, gain, strict=True)}
    except AttributeError:  # sklearn version without the attr
        importances = {name: 0.0 for name in feature_names}

    report = TrainingReport(
        n_samples=len(samples),
        n_train=fit_end,
        n_test=len(samples) - test_split,
        train_accuracy=train_acc,
        test_accuracy=float(cal["test_accuracy"]),
        test_log_loss=float(cal["test_log_loss"]),
        test_brier=float(cal["test_brier"]),
        horizon_bars=horizon_bars,
        feature_importances=importances,
        n_calibration=calib_size,
        test_brier_uncalibrated=float(cal["test_brier_uncalibrated"]),
        ece=float(cal["ece"]),
        ece_uncalibrated=float(cal["ece_uncalibrated"]),
        calibration_applied=bool(cal["calibration_applied"]),
    )

    # Capture the empirical p5/p95 envelope of every feature seen during
    # training (fit + calibration slices) so inference can flag out-of-regime.
    train_rows = rows[:test_split] if test_split <= len(rows) else rows
    distribution = build_feature_distribution(train_rows) if train_rows else None

    return SklearnForecaster(
        _classifier=clf,
        _horizon_bars=horizon_bars,
        _report=report,
        _distribution=distribution,
        _feature_names=feature_names,
        _news_feature_names=news_names,
        _macro_feature_names=macro_names,
        _calibrator=calibrator,
    )
