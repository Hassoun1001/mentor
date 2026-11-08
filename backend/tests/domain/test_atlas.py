"""The Methods Atlas: all 150 cards exist and every field is honestly filled."""

from __future__ import annotations

import re

import pytest

from mentor.domain.curriculum import ATLAS, CATALOG, USAGE_NOTE, get_lesson
from mentor.domain.curriculum.atlas.model import Group, Method
from mentor.domain.curriculum.model import Verdict
from mentor.domain.curriculum.sources import SOURCE_KEYS

EXPECTED: dict[str, tuple[str, ...]] = {
    "A": (
        "Support and Resistance",
        "Trend Analysis",
        "Price Action",
        "Dow Theory",
        "Elliott Wave",
        "Fibonacci Retracement",
        "Fibonacci Extension",
        "Fibonacci Expansion",
        "Fibonacci Time Zones",
        "Fibonacci Fan",
        "Gann Theory",
        "Harmonic Patterns",
        "Chart Patterns",
        "Candlestick Patterns",
        "Moving Averages",
        "Ichimoku",
        "Heikin-Ashi",
        "Renko",
        "Point and Figure",
        "Trendlines",
    ),
    "B": (
        "Wyckoff",
        "Smart Money Concepts",
        "ICT",
        "Order Blocks",
        "Fair Value Gaps",
        "Liquidity Sweeps",
        "Break of Structure",
        "Change of Character",
        "Market Structure Shift",
        "Supply and Demand Zones",
        "Stop Hunt Analysis",
        "Liquidity Pools",
        "Auction Market Theory",
        "Volume Spread Analysis",
        "Composite Operator Theory",
    ),
    "C": (
        "Volume Analysis",
        "Volume Profile",
        "Market Profile/TPO",
        "VWAP",
        "Anchored VWAP",
        "Order Book",
        "Depth of Market",
        "Footprint Charts",
        "Cumulative Volume Delta",
        "Open Interest",
        "Delta Analysis",
        "Tape Reading",
        "Time and Sales",
        "Order Flow Imbalance",
        "Liquidity Analysis",
    ),
    "D": (
        "RSI",
        "RSI Divergence",
        "MACD",
        "MACD Divergence",
        "Stochastic",
        "Bollinger Bands",
        "ATR",
        "ADX",
        "CCI",
        "Williams %R",
        "Parabolic SAR",
        "Keltner",
        "Donchian",
        "Rate of Change",
        "MFI",
        "OBV",
        "Chaikin Money Flow",
        "Aroon",
        "Supertrend",
        "MA Envelopes",
    ),
    "E": (
        "Fundamental Analysis",
        "Earnings",
        "Financial Statements",
        "DCF",
        "Relative Valuation",
        "Macroeconomic Analysis",
        "Interest Rates",
        "Inflation",
        "GDP",
        "Employment Data",
        "Central Bank Policy",
        "Yield Curve",
        "Bond Market",
        "DXY",
        "Commodity Supply and Demand",
        "Intermarket",
        "Geopolitical",
        "Economic Calendar Trading",
        "Liquidity Cycle",
        "Business Cycle",
    ),
    "F": (
        "Statistical Arbitrage",
        "Mean Reversion Models",
        "Momentum Models",
        "Pairs Trading",
        "Cointegration",
        "Regression",
        "Time-Series Analysis",
        "ARIMA",
        "GARCH",
        "Monte Carlo",
        "Bayesian Analysis",
        "Machine Learning",
        "Deep Learning",
        "Neural Networks",
        "Random Forest",
        "Gradient Boosting",
        "Reinforcement Learning",
        "High-Frequency Trading",
        "Market Making Algorithms",
        "Event-Driven Algorithms",
    ),
    "G": (
        "Implied Volatility",
        "Historical Volatility",
        "Volatility Surface",
        "Volatility Skew",
        "Delta Hedging",
        "Gamma Exposure",
        "Options Flow",
        "Put/Call Ratio",
        "Straddle",
        "Strangle",
        "Calendar Spreads",
        "Vertical Spreads",
        "Dispersion Trading",
        "Volatility Arbitrage",
        "Risk Reversal",
    ),
    "H": (
        "COT",
        "Fear and Greed Index",
        "News Sentiment",
        "Social Media Sentiment",
        "Institutional Positioning",
        "Short Interest",
        "Fund Flows",
        "ETF Flows",
        "Insider Transactions",
        "Analyst Revisions",
        "Positioning Extremes",
    ),
    "I": (
        "Position Sizing",
        "Kelly Criterion",
        "Fixed Fractional Risk",
        "Risk-to-Reward",
        "Diversification",
        "Correlation",
        "Portfolio Beta",
        "Value at Risk",
        "Expected Shortfall",
        "Maximum Drawdown",
        "Stop-Loss Placement",
        "Execution Algorithms",
        "TWAP",
        "Implementation Shortfall",
    ),
}

NEW_LESSONS = (
    "ta/dow-theory",
    "ta/stochastic",
    "ta/adx",
    "ta/donchian-channels",
    "ta/obv-and-mfi",
    "ta/harmonic-patterns",
    "ta/anchored-vwap",
    "smart-money/ict-terms",
    "flow/market-profile-and-auction-theory",
    "flow/cvd-and-footprint",
    "flow/tape-reading-and-dom",
    "options/implied-vs-historical-volatility",
    "options/straddles-and-strangles",
    "options/vertical-and-calendar-spreads",
    "options/delta-hedging-and-gamma",
    "options/volatility-skew-and-surface",
    "fundamentals/financial-statements",
    "fundamentals/dcf-and-relative-valuation",
    "fundamentals/earnings-and-the-drift",
    "macro/yield-curve",
    "macro/intermarket-analysis",
    "macro/business-and-liquidity-cycles",
    "macro/short-interest-insiders-flows",
    "risk/value-at-risk-and-expected-shortfall",
    "risk/beta",
)

ALL_CARDS: tuple[Method, ...] = tuple(method for group in ATLAS for method in group.methods)
_SENTENCE_END = re.compile(r"[.!?](?=\s|$)")
_ADVICE = re.compile(
    r"\b(buy now|sell now|you should (buy|sell)|guaranteed|risk[- ]free profit"
    r"|can.t lose|sure thing)\b",
    re.I,
)
_MEASURED = re.compile(r"\d\s*%|per ?cent", re.I)


def _by_letter() -> dict[str, Group]:
    return {group.letter: group for group in ATLAS}


def test_atlas_has_exactly_the_requested_150_methods() -> None:
    groups = _by_letter()
    assert sorted(groups) == list("ABCDEFGHI")
    assert sum(len(names) for names in EXPECTED.values()) == 150
    for letter, names in EXPECTED.items():
        assert tuple(method.name for method in groups[letter].methods) == names, letter


def test_card_slugs_are_unique() -> None:
    slugs = [method.slug for method in ALL_CARDS]
    assert len(set(slugs)) == 150


@pytest.mark.parametrize("method", ALL_CARDS, ids=lambda m: m.slug)
def test_every_field_is_filled(method: Method) -> None:
    for name in ("name", "what", "why", "when", "avoid", "tools", "evidence"):
        value = getattr(method, name)
        assert isinstance(value, str), name
        assert value.strip(), f"{method.name}: {name} is empty"
    assert method.users, method.name
    assert method.markets, method.name
    assert isinstance(method.verdict, Verdict), method.name


@pytest.mark.parametrize("method", ALL_CARDS, ids=lambda m: m.slug)
def test_card_text_keeps_its_promised_shape(method: Method) -> None:
    assert len(_SENTENCE_END.findall(method.what)) <= 2, f"{method.name}: 'what' is too long"
    assert len(_SENTENCE_END.findall(method.evidence)) == 1, f"{method.name}: one evidence sentence"


@pytest.mark.parametrize("method", ALL_CARDS, ids=lambda m: m.slug)
def test_usage_is_never_shown_as_a_measurement(method: Method) -> None:
    assert not _MEASURED.search(method.why), f"{method.name}: usage reason quotes a percentage"


@pytest.mark.parametrize("method", ALL_CARDS, ids=lambda m: m.slug)
def test_cards_do_not_recommend_trades_or_promise_profit(method: Method) -> None:
    for text in (method.what, method.why, method.when, method.avoid, method.evidence):
        assert not _ADVICE.search(text), f"{method.name}: {text}"


def test_card_links_and_sources_resolve() -> None:
    for method in ALL_CARDS:
        if method.lesson:
            assert get_lesson(method.lesson).slug == method.lesson
        assert set(method.sources) <= SOURCE_KEYS, method.name


def test_the_page_says_usage_labels_are_judgements() -> None:
    assert "informed judgements" in USAGE_NOTE
    assert "not measured percentages" in USAGE_NOTE
    assert "separate labels" in USAGE_NOTE


def test_new_lessons_exist_and_are_linked_from_the_atlas() -> None:
    assert 20 <= len(NEW_LESSONS) <= 25
    all_slugs = {lesson.slug for module in CATALOG for lesson in module.lessons}
    linked = {method.lesson for method in ALL_CARDS}
    for slug in NEW_LESSONS:
        assert slug in all_slugs
        assert slug in linked, f"no card links to {slug}"
