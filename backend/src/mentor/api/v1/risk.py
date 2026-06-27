"""Risk engine endpoints — Phase 0.

The thin transport layer: parse, hand to the domain, format. All business
logic lives in `mentor.domain.risk`; this module never does math.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from mentor.domain.instruments import BUILTIN_INSTRUMENTS, Instrument, get_instrument
from mentor.domain.money import Money, Percent
from mentor.domain.risk import (
    Direction,
    GuardrailLimits,
    OpenPosition,
    RiskInputs,
    calculate_position,
    check_guardrails,
    expectancy,
)

router = APIRouter(prefix="/risk", tags=["risk"])


# ---------- shared schemas ---------------------------------------------------


class MoneyDTO(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"amount": "10000", "currency": "USD"}})
    amount: Decimal = Field(
        ..., description="Decimal amount; use string form to avoid float noise."
    )
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 currency code.")

    def to_domain(self) -> Money:
        return Money(self.amount, self.currency)


# ---------- position sizing --------------------------------------------------


class PositionSizeRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "EURUSD",
                "account": {"amount": "10000", "currency": "USD"},
                "risk_percent": "1",
                "direction": "long",
                "entry": "1.08500",
                "stop": "1.08200",
                "target": "1.09100",
                "quote_to_account_rate": "1",
            }
        }
    )

    symbol: str = Field(..., examples=["EURUSD"])
    account: MoneyDTO
    risk_percent: Annotated[Decimal, Field(gt=0, le=10, description="Risk as %, e.g. 1 for 1%.")]
    direction: Direction
    entry: Annotated[Decimal, Field(gt=0)]
    stop: Annotated[Decimal, Field(gt=0)]
    target: Annotated[Decimal | None, Field(gt=0)] = None
    quote_to_account_rate: Annotated[Decimal, Field(gt=0)] = Decimal("1")


class PositionSizeResponse(BaseModel):
    symbol: str
    direction: Direction
    lots: Decimal
    units: Decimal
    pip_distance: Decimal
    pip_value_in_account: MoneyDTO
    money_at_risk: MoneyDTO
    risk_pct_of_account: Decimal
    risk_reward_ratio: Decimal | None
    notional_in_quote: Decimal
    raw_lots_before_rounding: Decimal
    is_aggressive: bool
    notes: list[str]


@router.post(
    "/position-size",
    response_model=PositionSizeResponse,
    summary="Size a trade from account risk %, stop distance, and pip value.",
)
async def position_size(body: PositionSizeRequest) -> PositionSizeResponse:
    inputs = RiskInputs(
        account_balance=body.account.to_domain(),
        risk=Percent.from_percent(body.risk_percent),
        entry=body.entry,
        stop=body.stop,
        target=body.target,
        direction=body.direction,
        instrument=get_instrument(body.symbol),
        quote_to_account_rate=body.quote_to_account_rate,
    )
    result = calculate_position(inputs)
    return PositionSizeResponse(
        symbol=inputs.instrument.symbol,
        direction=body.direction,
        lots=result.lots,
        units=result.units,
        pip_distance=result.pip_distance,
        pip_value_in_account=MoneyDTO(
            amount=result.pip_value_in_account.amount,
            currency=result.pip_value_in_account.currency,
        ),
        money_at_risk=MoneyDTO(
            amount=result.money_at_risk.amount,
            currency=result.money_at_risk.currency,
        ),
        risk_pct_of_account=result.money_at_risk_pct.as_percent,
        risk_reward_ratio=result.risk_reward_ratio,
        notional_in_quote=result.notional_in_quote,
        raw_lots_before_rounding=result.raw_lots_before_rounding,
        is_aggressive=result.is_aggressive,
        notes=list(result.notes),
    )


# ---------- expectancy -------------------------------------------------------


class ExpectancyRequest(BaseModel):
    win_rate_percent: Annotated[Decimal, Field(ge=0, le=100)]
    avg_win_r: Annotated[Decimal, Field(ge=0)]
    avg_loss_r: Annotated[Decimal, Field(ge=0, description="Magnitude, not signed.")]
    sample_size: int = 0


class ExpectancyResponse(BaseModel):
    expected_value_r: Decimal
    profit_factor: Decimal | None
    is_positive: bool
    interpretation: str


@router.post(
    "/expectancy",
    response_model=ExpectancyResponse,
    summary="Compute per-trade expectancy in R-multiples.",
)
async def post_expectancy(body: ExpectancyRequest) -> ExpectancyResponse:
    result = expectancy(
        win_rate=Percent.from_percent(body.win_rate_percent),
        avg_win_r=body.avg_win_r,
        avg_loss_r=body.avg_loss_r,
        sample_size=body.sample_size,
    )
    if result.expected_value_r > Decimal("0.2"):
        interp = "Strong positive edge in R-multiples — backtest it honestly before trusting it."
    elif result.expected_value_r > 0:
        interp = "Marginal positive edge — small enough that costs and slippage can erase it."
    elif result.expected_value_r == 0:
        interp = "Break-even expectancy — no edge once you account for variance."
    else:
        interp = "Negative expectancy — this strategy loses money over many trades."
    return ExpectancyResponse(
        expected_value_r=result.expected_value_r,
        profit_factor=result.profit_factor,
        is_positive=result.is_positive,
        interpretation=interp,
    )


# ---------- guardrails -------------------------------------------------------


class OpenPositionDTO(BaseModel):
    money_at_risk: MoneyDTO


class GuardrailCheckRequest(BaseModel):
    account: MoneyDTO
    max_risk_per_trade_percent: Annotated[Decimal, Field(gt=0, le=10)]
    max_open_risk_percent: Annotated[Decimal, Field(gt=0, le=25)]
    daily_loss_limit_percent: Annotated[Decimal, Field(gt=0, le=25)]
    prospective_trade_risk: MoneyDTO
    open_positions: list[OpenPositionDTO] = Field(default_factory=list)
    realised_pnl_today: MoneyDTO | None = None


class BreachDTO(BaseModel):
    kind: Literal["per_trade", "open_risk", "daily_loss"]
    message: str
    current_percent: Decimal
    limit_percent: Decimal


class GuardrailCheckResponse(BaseModel):
    passed: bool
    breaches: list[BreachDTO]
    open_risk_percent: Decimal
    daily_loss_percent: Decimal
    prospective_trade_risk_percent: Decimal
    notes: list[str]


@router.post(
    "/guardrails",
    response_model=GuardrailCheckResponse,
    summary="Check a prospective trade against per-trade, portfolio, and daily limits.",
)
async def guardrails(body: GuardrailCheckRequest) -> GuardrailCheckResponse:
    limits = GuardrailLimits(
        max_risk_per_trade=Percent.from_percent(body.max_risk_per_trade_percent),
        max_open_risk=Percent.from_percent(body.max_open_risk_percent),
        daily_loss_limit=Percent.from_percent(body.daily_loss_limit_percent),
    )
    report = check_guardrails(
        account_balance=body.account.to_domain(),
        limits=limits,
        prospective_trade_risk=body.prospective_trade_risk.to_domain(),
        open_positions=[
            OpenPosition(money_at_risk=p.money_at_risk.to_domain()) for p in body.open_positions
        ],
        realised_pnl_today=body.realised_pnl_today.to_domain() if body.realised_pnl_today else None,
    )
    return GuardrailCheckResponse(
        passed=report.passed,
        breaches=[
            BreachDTO(
                kind=b.kind.value,
                message=b.message,
                current_percent=b.current * Decimal("100"),
                limit_percent=b.limit * Decimal("100"),
            )
            for b in report.breaches
        ],
        open_risk_percent=report.open_risk_pct.as_percent,
        daily_loss_percent=report.daily_loss_pct.as_percent,
        prospective_trade_risk_percent=report.prospective_trade_risk_pct.as_percent,
        notes=list(report.notes),
    )


# ---------- instruments ------------------------------------------------------


class InstrumentDTO(BaseModel):
    symbol: str
    base: str
    quote: str
    pip_size: Decimal
    contract_size: Decimal
    min_lot: Decimal
    lot_step: Decimal

    @classmethod
    def from_domain(cls, i: Instrument) -> InstrumentDTO:
        return cls(
            symbol=i.symbol,
            base=i.base,
            quote=i.quote,
            pip_size=i.pip_size,
            contract_size=i.contract_size,
            min_lot=i.min_lot,
            lot_step=i.lot_step,
        )


@router.get(
    "/instruments", response_model=list[InstrumentDTO], summary="List built-in instruments."
)
async def list_instruments() -> list[InstrumentDTO]:
    return [InstrumentDTO.from_domain(i) for i in BUILTIN_INSTRUMENTS.values()]
