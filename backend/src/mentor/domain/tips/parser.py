"""Tip parser contract.

A tipster's message is unstructured prose — tickers scattered across
category headers with parenthetical commentary. Turning that into
structured `ParsedTip`s is a language task, so the concrete implementation
is LLM-backed (in the infrastructure layer). The domain only knows the
contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from mentor.domain.tips.tip import ParsedTip


class TipParser(ABC):
    @abstractmethod
    async def parse(self, *, text: str) -> Sequence[ParsedTip]:
        """Extract every actionable tip from a raw message."""
        ...
