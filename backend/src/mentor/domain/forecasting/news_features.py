"""News-sentiment features — point-in-time, lookahead-safe.

These augment the technical feature set with the *news regime*: how
negative/positive coverage has been, how loud it's been, and whether
sentiment is turning. They're derived from a daily tone series (GDELT)
and, like every other feature, computed strictly from data on or before
the as-of bar — at a daily bar that closes at end of day D, the news of
day D is already public, so day ≤ D is fair game; day > D is not.

The features are deliberately few and interpretable:

- ``news_tone``      — most recent day's average tone, scaled to ~[-1, 1]
- ``news_tone_5d``   — 5-day mean tone (the prevailing mood)
- ``news_tone_mom``  — today's tone minus the 5-day mean (is it turning?)
- ``news_vol_5d``    — 5-day mean news volume (how loud the flow is)

When there's no news on/before the as-of date the features are neutral
zeros — the same as "no information," which is honest.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Final

NEWS_FEATURE_NAMES: Final[tuple[str, ...]] = (
    "news_tone",
    "news_tone_5d",
    "news_tone_mom",
    "news_vol_5d",
)

# GDELT Average Tone is roughly [-10, +10]; divide to land near [-1, 1].
_TONE_SCALE = 10.0
_WINDOW = 5

_NEUTRAL: Final[dict[str, float]] = dict.fromkeys(NEWS_FEATURE_NAMES, 0.0)


@dataclass(frozen=True, slots=True)
class NewsTonePoint:
    day: datetime  # midnight UTC of the news day
    tone: float
    volume: float


class NewsToneSeries:
    """An ascending-by-day tone series with point-in-time feature lookup."""

    def __init__(self, points: Sequence[NewsTonePoint]) -> None:
        self._points = sorted(points, key=lambda p: p.day)

    def __len__(self) -> int:
        return len(self._points)

    @property
    def empty(self) -> bool:
        return not self._points

    def features_asof(self, ts: datetime) -> dict[str, float]:
        """News features using only days on or before ``ts``'s date."""
        if not self._points:
            return dict(_NEUTRAL)
        cutoff = ts
        # Visible = points whose day <= the as-of date (date-level compare).
        visible = [p for p in self._points if p.day.date() <= cutoff.date()]
        if not visible:
            return dict(_NEUTRAL)

        window = visible[-_WINDOW:]
        tone_now = visible[-1].tone / _TONE_SCALE
        tone_5d = sum(p.tone for p in window) / len(window) / _TONE_SCALE
        vol_5d = sum(p.volume for p in window) / len(window)
        return {
            "news_tone": _clip(tone_now),
            "news_tone_5d": _clip(tone_5d),
            "news_tone_mom": _clip(tone_now - tone_5d),
            "news_vol_5d": vol_5d,
        }


def _clip(value: float, lo: float = -3.0, hi: float = 3.0) -> float:
    return max(lo, min(hi, value))
