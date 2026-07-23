"""Journal domain — Phase 1.

> The user's win rate, expectancy, and R-multiple distribution — the real
> measure of progress.   — Mentor product plan, §6.F
"""

from mentor.domain.journal.analytics import JournalAnalytics, compute_analytics
from mentor.domain.journal.checklist import (
    ChecklistResult,
    PreTradeChecklist,
    evaluate_pre_trade_checklist,
)
from mentor.domain.journal.mistakes import (
    MistakeDefinition,
    MistakeTag,
    RootCause,
    RootCauseBreakdown,
    compute_root_causes,
    definition_for,
    mistake_catalog,
    normalise_tags,
)
from mentor.domain.journal.trade import (
    Trade,
    TradePlan,
    TradeStatus,
    close_trade,
    open_trade,
    plan_trade,
)

__all__ = [
    "ChecklistResult",
    "JournalAnalytics",
    "MistakeDefinition",
    "MistakeTag",
    "PreTradeChecklist",
    "RootCause",
    "RootCauseBreakdown",
    "Trade",
    "TradePlan",
    "TradeStatus",
    "close_trade",
    "compute_analytics",
    "compute_root_causes",
    "definition_for",
    "evaluate_pre_trade_checklist",
    "mistake_catalog",
    "normalise_tags",
    "open_trade",
    "plan_trade",
]
