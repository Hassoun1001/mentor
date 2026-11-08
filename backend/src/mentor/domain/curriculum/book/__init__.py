"""The book, in reading order: one file per stage of the path."""

from __future__ import annotations

from typing import Final

from mentor.domain.curriculum.book import (
    part01_start,
    part02_markets,
    part03_charts,
    part04_risk,
)
from mentor.domain.curriculum.model import Module, Part

PARTS: Final[tuple[Part, ...]] = (
    Part(
        "start",
        1,
        "Stage 1",
        "Absolute basics",
        "What trading is, what you are buying, and the honest odds.",
    ),
    Part(
        "markets",
        2,
        "Stage 2",
        "How markets and orders work",
        "Who trades, how an order gets filled, and what it costs.",
    ),
    Part(
        "charts",
        3,
        "Stage 3",
        "Charts and candles",
        "How to read what a chart is really telling you.",
    ),
    Part(
        "risk",
        4,
        "Stage 4",
        "Risk and position sizing",
        "How to survive. Learn this before any strategy.",
    ),
    Part(
        "technical",
        5,
        "Stage 5",
        "Technical analysis",
        "Levels, patterns, indicators and theories, each tested honestly.",
    ),
    Part(
        "macro",
        6,
        "Stage 6",
        "Fundamentals and macro",
        "Central banks, data and the forces that move whole markets.",
    ),
    Part(
        "plans",
        7,
        "Stage 7",
        "Trading plans",
        "Every major way to trade, with full rules and when each one fails.",
    ),
    Part(
        "every-market",
        8,
        "Stage 8",
        "Market by market",
        "How forex, stocks, futures, gold, bonds, options and crypto differ.",
    ),
    Part(
        "mind",
        9,
        "Stage 9",
        "Psychology and journaling",
        "Your behaviour is the biggest risk in the whole system.",
    ),
    Part("testing", 10, "Stage 10", "Testing and statistics", "How to tell a real edge from luck."),
    Part(
        "algos",
        11,
        "Stage 11",
        "Algorithms and prediction",
        "Models, machine learning and execution algorithms.",
    ),
    Part(
        "pro",
        12,
        "Stage 12",
        "Running it as a professional",
        "Routine, prop firms, tax, regulation and going live.",
    ),
    Part(
        "mentor",
        13,
        "Inside this app",
        "How the mentor works",
        "How this app predicts, grades itself and stays honest.",
    ),
)

BOOK_MODULES: Final[tuple[Module, ...]] = (
    *part01_start.CHAPTERS,
    *part02_markets.CHAPTERS,
    *part03_charts.CHAPTERS,
    *part04_risk.CHAPTERS,
)
