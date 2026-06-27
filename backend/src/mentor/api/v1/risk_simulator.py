"""Risk-of-ruin Monte Carlo endpoint."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from mentor.api.deps import SessionDep
from mentor.domain.errors import ValidationError
from mentor.domain.risk import simulate_risk_of_ruin
from mentor.infrastructure.repositories import TradeRepository

router = APIRouter(prefix="/risk/monte-carlo", tags=["risk"])


class MonteCarloRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "starting_balance": "10000",
                "risk_per_trade_percent": "1",
                "n_trades": 200,
                "n_runs": 5000,
                "ruin_fraction": "0.5",
                "use_journal": True,
            }
        }
    )

    starting_balance: Annotated[Decimal, Field(gt=0)]
    risk_per_trade_percent: Annotated[Decimal, Field(gt=0, le=20)]
    n_trades: Annotated[int, Field(ge=10, le=2000)] = 200
    n_runs: Annotated[int, Field(ge=100, le=50_000)] = 5_000
    ruin_fraction: Annotated[Decimal, Field(ge=Decimal("0.1"), le=Decimal("0.9"))] = Decimal("0.5")
    use_journal: bool = True
    fallback_distribution: list[Decimal] | None = None  # used if journal is empty


class MonteCarloResponse(BaseModel):
    n_runs: int
    n_trades: int
    sample_size: int
    risk_per_trade_pct: Decimal
    starting_balance: Decimal
    ruin_threshold: Decimal
    probability_of_ruin: Decimal
    median_terminal: Decimal
    p5_terminal: Decimal
    p95_terminal: Decimal
    median_max_drawdown_pct: Decimal
    p95_max_drawdown_pct: Decimal
    expected_terminal: Decimal
    used_journal: bool


@router.post("", response_model=MonteCarloResponse)
async def monte_carlo(body: MonteCarloRequest, session: SessionDep) -> MonteCarloResponse:
    pool: list[Decimal] = []
    used_journal = False

    if body.use_journal:
        closed = await TradeRepository(session).list_closed()
        pool = [t.realised_r for t in closed if t.realised_r is not None]
        used_journal = bool(pool)

    if not pool:
        if not body.fallback_distribution:
            raise HTTPException(
                status_code=400,
                detail=(
                    "no closed trades in journal — provide fallback_distribution "
                    "(e.g. [-1, -1, 2] for a 33%/67% win/loss demo)"
                ),
            )
        pool = list(body.fallback_distribution)

    try:
        result = simulate_risk_of_ruin(
            r_distribution=pool,
            starting_balance=body.starting_balance,
            risk_per_trade_fraction=body.risk_per_trade_percent / Decimal("100"),
            n_trades=body.n_trades,
            n_runs=body.n_runs,
            ruin_fraction=body.ruin_fraction,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return MonteCarloResponse(
        n_runs=result.n_runs,
        n_trades=result.n_trades,
        sample_size=len(pool),
        risk_per_trade_pct=result.risk_per_trade_pct,
        starting_balance=result.starting_balance,
        ruin_threshold=result.ruin_threshold,
        probability_of_ruin=result.probability_of_ruin,
        median_terminal=result.median_terminal,
        p5_terminal=result.p5_terminal,
        p95_terminal=result.p95_terminal,
        median_max_drawdown_pct=result.median_max_drawdown_pct,
        p95_max_drawdown_pct=result.p95_max_drawdown_pct,
        expected_terminal=result.expected_terminal,
        used_journal=used_journal,
    )
