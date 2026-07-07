"""Leaderboard — rank every tipster's track record, risk-adjusted."""

from __future__ import annotations

from mentor.application.tips.scoring_service import TipScoringService
from mentor.domain.tips.leaderboard import LeaderboardRow, build_leaderboard


class LeaderboardService:
    def __init__(self, *, scoring: TipScoringService) -> None:
        self._scoring = scoring

    async def rank(self) -> tuple[LeaderboardRow, ...]:
        grouped = await self._scoring.outcomes_by_tipster()
        return build_leaderboard(grouped)
