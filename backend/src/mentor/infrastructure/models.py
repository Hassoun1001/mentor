"""ORM models.

Models are versioned in this single module so Alembic autogeneration sees
them in one import. The application layer never imports these directly —
repositories translate between ORM rows and domain objects.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mentor.infrastructure.db import Base

if TYPE_CHECKING:
    pass


# --- timestamp mixin --------------------------------------------------------


class _TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# --- price bar (TimescaleDB hypertable) ------------------------------------


class PriceBar(Base):
    """One OHLCV candle at a specific timeframe.

    Stored as a TimescaleDB hypertable partitioned on `ts`. The primary key
    `(symbol, timeframe, ts)` doubles as a uniqueness guarantee so the
    ingestion worker can safely re-fetch overlapping ranges (idempotency).
    """

    __tablename__ = "price_bars"

    symbol: Mapped[str] = mapped_column(String(16), primary_key=True)
    timeframe: Mapped[str] = mapped_column(String(8), primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    open: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    volume: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint("high >= low", name="ck_price_bars_high_ge_low"),
        CheckConstraint("high >= open AND high >= close", name="ck_price_bars_high_envelope"),
        CheckConstraint("low <= open AND low <= close", name="ck_price_bars_low_envelope"),
        Index("ix_price_bars_symbol_ts_desc", "symbol", "timeframe", ts.desc()),
    )


# --- trade journal ----------------------------------------------------------


class Trade(Base, _TimestampMixin):
    """A paper or live trade.

    Lifecycle: `planned` → `open` → `closed`, or `planned` → `cancelled`.
    R-multiple is recomputed deterministically from the stored fields
    whenever a trade reaches `closed`; it is not user-editable.
    """

    __tablename__ = "trades"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
    direction: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="planned")

    size_lots: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    planned_entry: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    planned_stop: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    planned_target: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)

    actual_entry: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    actual_exit: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    entry_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    exit_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    initial_risk_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    risk_currency: Mapped[str] = mapped_column(String(3), nullable=False)

    realised_pnl: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    realised_r: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)

    reflection: Mapped[JournalReflection | None] = relationship(
        back_populates="trade",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint("direction IN ('long','short')", name="ck_trades_direction"),
        CheckConstraint(
            "status IN ('planned','open','closed','cancelled')",
            name="ck_trades_status",
        ),
        CheckConstraint("size_lots >= 0", name="ck_trades_size_nonneg"),
        CheckConstraint("planned_entry > 0 AND planned_stop > 0", name="ck_trades_prices_positive"),
        Index("ix_trades_symbol_status_created", "symbol", "status", "created_at"),
    )


class JournalReflection(Base, _TimestampMixin):
    """The user's reflection on a trade — the discipline layer.

    `reason` is required at plan-time (the pre-trade checklist enforces it);
    `mistake_tags` and `emotion` are filled post-close.
    """

    __tablename__ = "journal_reflections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trades.id", ondelete="CASCADE"), unique=True
    )

    reason: Mapped[str] = mapped_column(Text, nullable=False)
    mistake_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(32)), server_default="{}", nullable=False
    )
    emotion: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    trade: Mapped[Trade] = relationship(back_populates="reflection")


# --- curriculum progress ----------------------------------------------------


class LessonProgress(Base, _TimestampMixin):
    """User-side progress through a code-shipped lesson.

    The lessons themselves live in `mentor.domain.curriculum.catalog` — only
    progress is persisted. The `lesson_slug` is the FK *into the code*, not
    a real database FK; deleting a lesson from the catalog is a deliberate
    code change.
    """

    __tablename__ = "lesson_progress"

    lesson_slug: Mapped[str] = mapped_column(String(128), primary_key=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="in_progress")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('not_started','in_progress','completed')",
            name="ck_lesson_progress_status",
        ),
    )


# --- news items -------------------------------------------------------------


class NewsItemORM(Base, _TimestampMixin):
    __tablename__ = "news_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    category: Mapped[str | None] = mapped_column(String(16), nullable=True)
    impact: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    classified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "category IS NULL OR category IN "
            "('macro','regulatory','geopolitical','risk-off','hype','other')",
            name="ck_news_items_category",
        ),
        Index("ix_news_items_ts_desc", ts.desc()),
    )


# --- daily news tone (GDELT) ------------------------------------------------


class DailyNewsToneORM(Base, _TimestampMixin):
    """One day's aggregate news sentiment for a macro query (GDELT).

    `tone` is GDELT's Average Tone (roughly -10..+10; negative = more
    negative coverage). `volume` is GDELT's Volume Intensity (share of
    global coverage matching the query). Keyed by (query_key, day) so we
    can hold tone series for more than one query later. This is a derived
    cache backfilled from GDELT — not user data — but persisted so the
    model trains without re-hitting the rate-limited API every run.
    """

    __tablename__ = "daily_news_tone"

    query_key: Mapped[str] = mapped_column(String(32), primary_key=True)
    day: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    tone: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    volume: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    article_count: Mapped[int] = mapped_column(nullable=False, default=0)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="gdelt")

    __table_args__ = (Index("ix_daily_news_tone_day", "query_key", day.desc()),)


class MacroSeriesORM(Base, _TimestampMixin):
    """One daily observation of a macro/FX-driver series (FRED cache).

    Keyed by (series_id, day) so a single table holds every driver — US
    rates, the 2s10s curve, the broad dollar index, VIX. A derived cache
    backfilled from FRED (not user data), persisted so the model trains
    without re-hitting the network — mirrors ``daily_news_tone``.
    """

    __tablename__ = "macro_series"

    series_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    day: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="fred")

    __table_args__ = (Index("ix_macro_series_day", "series_id", day.desc()),)


# --- stock tips (tipster track record) -------------------------------------


class StockTipORM(Base, _TimestampMixin):
    """One actionable stock tip from a tipster, with the entry price
    snapshotted at the mention date so returns can be scored later."""

    __tablename__ = "stock_tips"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipster: Mapped[str] = mapped_column(String(64), nullable=False)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    category: Mapped[str] = mapped_column(String(24), nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    conviction: Mapped[str] = mapped_column(String(8), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False, server_default="")

    raw_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    mentioned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    mention_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="USD")
    source: Mapped[str] = mapped_column(String(16), nullable=False, server_default="yahoo")

    __table_args__ = (
        CheckConstraint(
            "action IN ('buy','buy_on_dip','hold','watch','avoid')",
            name="ck_stock_tips_action",
        ),
        Index("ix_stock_tips_tipster_ticker", "tipster", "ticker"),
        Index("ix_stock_tips_mentioned_at", mentioned_at.desc()),
    )


# --- predictions (audit log) -----------------------------------------------


class PredictionORM(Base, _TimestampMixin):
    """Every forecast is logged here, and the resolver fills realised
    outcome once the horizon elapses. This is the calibration loop the
    plan calls out in §6.I — "every forecast logged against its real outcome.\""""

    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    asof: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    asof_close: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    horizon_bars: Mapped[int] = mapped_column(nullable=False)
    horizon_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    p_up: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    direction: Mapped[str] = mapped_column(String(8), nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)

    # JSON snapshot of the features used — for audit, not derivation
    features_json: Mapped[str] = mapped_column(Text, nullable=False)

    # 'live' = predicted forward, in real time, before the outcome existed.
    # 'replay' = backfilled over history. Both are point-in-time in their
    # feature construction, but only 'live' is a track record — mixing them
    # silently inflates every scoreboard in the app.
    origin: Mapped[str] = mapped_column(String(16), nullable=False, default="live")

    realised_close: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    realised_outcome: Mapped[int | None] = mapped_column(nullable=True)  # 1 = up, 0 = not up
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("direction IN ('long','short','neutral')", name="ck_predictions_direction"),
        CheckConstraint("p_up >= 0 AND p_up <= 1", name="ck_predictions_p_up"),
        CheckConstraint("origin IN ('live','replay')", name="ck_predictions_origin"),
        Index("ix_predictions_symbol_asof", "symbol", asof.desc()),
        Index("ix_predictions_unresolved", "horizon_at", "resolved_at"),
    )


# --- alerts -----------------------------------------------------------------


class AlertORM(Base, _TimestampMixin):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="armed")
    condition_json: Mapped[str] = mapped_column(Text, nullable=False)
    fired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_evaluated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        CheckConstraint(
            "kind IN ('price_above','price_below','signal_change','event_freeze')",
            name="ck_alerts_kind",
        ),
        CheckConstraint("status IN ('armed','fired','disabled')", name="ck_alerts_status"),
        Index("ix_alerts_status", "status"),
    )


# --- economic calendar -----------------------------------------------------


class EconomicEventORM(Base, _TimestampMixin):
    __tablename__ = "economic_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    external_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    country: Mapped[str] = mapped_column(String(8), nullable=False)
    impact: Mapped[int] = mapped_column(nullable=False)  # 1 / 2 / 3
    forecast: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous: Mapped[str | None] = mapped_column(Text, nullable=True)
    actual: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("impact IN (1,2,3)", name="ck_economic_events_impact"),
        Index("ix_economic_events_ts", ts),
        Index("ix_economic_events_country_ts", "country", ts),
    )


class UserORM(Base, _TimestampMixin):
    """Login accounts. The first row is seeded from the env-configured
    admin credentials on first login; everyone else is created in-app.
    `allowed_tabs` is a JSON list of UI tab ids, or the literal "*" for all."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    is_admin: Mapped[bool] = mapped_column(nullable=False, default=False)
    allowed_tabs: Mapped[str] = mapped_column(Text, nullable=False, default="*")
