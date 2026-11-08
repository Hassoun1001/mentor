"""The building blocks of the Methods Atlas.

The Atlas is a reference page: one short card for each named trading method.
Two labels are kept apart on purpose. ``Usage`` says how many people use a
method. ``Verdict`` says whether it holds up when tested. A method can be very
popular and still have weak evidence, and the page must never blur the two.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from mentor.domain.curriculum.model import Verdict


class Usage(StrEnum):
    """An informed judgement of how widely a method is used. Never a measurement."""

    VERY_COMMON = "very_common"
    COMMON = "common"
    SPECIALIST = "specialist"
    RARE = "rare"


class Trader(StrEnum):
    RETAIL = "retail"
    PROP = "prop"
    FUNDS = "funds"
    BANKS = "banks"
    MARKET_MAKERS = "market_makers"


class Market(StrEnum):
    FOREX = "forex"
    STOCKS = "stocks"
    INDICES = "indices"
    FUTURES = "futures"
    COMMODITIES = "commodities"
    BONDS = "bonds"
    OPTIONS = "options"
    CRYPTO = "crypto"


class Access(StrEnum):
    """Can a normal retail trader get what the method needs?"""

    EASY = "easy"  # free, or included with a normal broker or charting account
    PAID = "paid"  # yes, but it costs money or needs a specialist feed
    HARD = "hard"  # in practice only firms have it


@dataclass(frozen=True, slots=True, kw_only=True)
class Method:
    """One card. Every field except ``lesson`` and ``sources`` must be filled."""

    name: str
    what: str
    users: tuple[Trader, ...]
    usage: Usage
    why: str  # the reasoning behind the usage label
    when: str
    avoid: str
    markets: tuple[Market, ...]
    tools: str
    access: Access
    verdict: Verdict
    evidence: str  # one sentence
    lesson: str = ""  # slug of the full lesson, when one exists
    sources: tuple[str, ...] = ()

    @property
    def slug(self) -> str:
        return re.sub(r"[^a-z0-9]+", "-", self.name.lower()).strip("-")


@dataclass(frozen=True, slots=True)
class Group:
    letter: str
    title: str
    summary: str
    methods: tuple[Method, ...]


# Short names so the card files read like a table.
R = Trader.RETAIL
P = Trader.PROP
F = Trader.FUNDS
B = Trader.BANKS
MM = Trader.MARKET_MAKERS

VERY_COMMON = Usage.VERY_COMMON
COMMON = Usage.COMMON
SPECIALIST = Usage.SPECIALIST
RARE = Usage.RARE

EASY = Access.EASY
PAID = Access.PAID
HARD = Access.HARD

FACT = Verdict.FACT
SUPPORTED = Verdict.SUPPORTED
MIXED = Verdict.MIXED
WEAK = Verdict.WEAK
UNTESTED = Verdict.UNTESTED

FX = Market.FOREX
STOCKS = Market.STOCKS
INDICES = Market.INDICES
FUTURES = Market.FUTURES
COMMODITIES = Market.COMMODITIES
BONDS = Market.BONDS
OPTIONS = Market.OPTIONS
CRYPTO = Market.CRYPTO

LIQUID = (FX, STOCKS, INDICES, FUTURES, COMMODITIES, CRYPTO)
EVERY = (FX, STOCKS, INDICES, FUTURES, COMMODITIES, BONDS, OPTIONS, CRYPTO)
EXCHANGE = (STOCKS, INDICES, FUTURES, COMMODITIES)
