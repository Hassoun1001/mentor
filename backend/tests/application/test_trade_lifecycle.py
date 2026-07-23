"""Plan → open → close → diagnose, as one chain.

Each piece of the journal was tested in isolation — the trade state machine,
the mistake taxonomy, the analytics — but nothing exercised them together.
So nothing would have caught a break *between* them: a loss closed with tags
that never reaches the root-cause review, an R-multiple that survives the
domain but is dropped on the way to the scoreboard, a review that ranks a
cause the trade was never tagged with.

The API layer cannot be tested here (the endpoints need Postgres, and the
shared client fixture has no database), so this runs against the service
with a fake repository. That covers everything except the HTTP shell.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from mentor.application.journal import TradeService
from mentor.domain.errors import ValidationError
from mentor.domain.instruments import get_instrument
from mentor.domain.journal.mistakes import (
    MistakeTag,
    compute_root_causes,
    normalise_tags,
)
from mentor.domain.journal.trade import Trade, TradePlan, TradeStatus
from mentor.domain.money import Money
from mentor.domain.risk.position_sizing import Direction


class _FakeTradeRepo:
    """In-memory stand-in for TradeRepository."""

    def __init__(self) -> None:
        self._rows: dict[uuid.UUID, Trade] = {}

    async def add(self, trade: Trade) -> Trade:
        self._rows[trade.id] = trade
        return trade

    async def get(self, trade_id: uuid.UUID) -> Trade | None:
        return self._rows.get(trade_id)

    async def save(self, trade: Trade) -> Trade:
        self._rows[trade.id] = trade
        return trade

    async def list_closed(self, *, symbol: str | None = None) -> list[Trade]:
        return [
            t
            for t in self._rows.values()
            if t.status is TradeStatus.CLOSED and (symbol is None or t.symbol == symbol)
        ]

    async def list_recent(self, *, symbol: str | None = None, limit: int = 100) -> list[Trade]:
        return list(self._rows.values())[:limit]


def _plan(direction: Direction = Direction.LONG) -> TradePlan:
    long = direction is Direction.LONG
    return TradePlan(
        symbol="EURUSD",
        direction=direction,
        size_lots=Decimal("0.10"),
        entry=Decimal("1.1000"),
        stop=Decimal("1.0950") if long else Decimal("1.1050"),
        target=Decimal("1.1100") if long else Decimal("1.0900"),
        initial_risk=Money(Decimal("50"), "USD"),
        reason="testing the chain end to end",
    )


@pytest.fixture
def service() -> TradeService:
    return TradeService(_FakeTradeRepo())  # type: ignore[arg-type]


# ---------- the happy path ----------


async def test_a_losing_trade_reaches_the_root_cause_review(service: TradeService) -> None:
    """The whole point of the journal: a tagged loss must become a diagnosis."""
    planned = await service.plan(_plan())
    await service.open(planned.id, fill_price=Decimal("1.1000"))

    # Stopped out: 50 pips against on a 50-pip risk = -1R.
    closed = await service.close(
        planned.id,
        exit_price=Decimal("1.0950"),
        mistake_tags=normalise_tags(["moved_stop", "oversized"]),
    )

    assert closed.status is TradeStatus.CLOSED
    assert closed.realised_r is not None
    assert closed.realised_r < 0

    review = compute_root_causes([closed])
    assert review.closed_losses == 1
    assert review.tagged_losses == 1
    assert review.process_error_losses == 1
    assert {c.tag for c in review.causes} == {MistakeTag.MOVED_STOP, MistakeTag.OVERSIZED}
    # Ranked by damage, and a multi-tag loss attributes its full R to each.
    assert all(c.r_lost == abs(closed.realised_r) for c in review.causes)


async def test_a_winner_is_never_diagnosed_as_a_mistake(service: TradeService) -> None:
    planned = await service.plan(_plan())
    await service.open(planned.id, fill_price=Decimal("1.1000"))
    closed = await service.close(planned.id, exit_price=Decimal("1.1100"))

    assert closed.realised_r is not None and closed.realised_r > 0
    assert compute_root_causes([closed]).closed_losses == 0


async def test_the_r_multiple_survives_the_whole_chain(service: TradeService) -> None:
    """A 100-pip win on a 50-pip risk is +2R, computed from the row itself."""
    instrument = get_instrument("EURUSD")
    planned = await service.plan(_plan())
    await service.open(planned.id, fill_price=Decimal("1.1000"))
    closed = await service.close(planned.id, exit_price=Decimal("1.1100"))

    units = Decimal("0.10") * instrument.contract_size
    expected_pnl = Decimal("0.0100") * units  # 100 pips
    assert closed.realised_pnl is not None
    assert closed.realised_pnl.amount == expected_pnl.quantize(Decimal("0.01"))
    assert closed.realised_r == expected_pnl.quantize(Decimal("0.01")) / Decimal("50")


async def test_a_short_is_symmetric(service: TradeService) -> None:
    planned = await service.plan(_plan(Direction.SHORT))
    await service.open(planned.id, fill_price=Decimal("1.1000"))
    closed = await service.close(planned.id, exit_price=Decimal("1.0900"))  # +100 pips

    assert closed.realised_r is not None and closed.realised_r > 0


# ---------- analytics see what the journal recorded ----------


async def test_analytics_count_only_closed_trades(service: TradeService) -> None:
    open_only = await service.plan(_plan())
    await service.open(open_only.id, fill_price=Decimal("1.1000"))

    done = await service.plan(_plan())
    await service.open(done.id, fill_price=Decimal("1.1000"))
    await service.close(done.id, exit_price=Decimal("1.1100"))

    a = await service.analytics()
    assert a.sample_size == 1  # the still-open trade is not a result
    assert a.wins == 1


# ---------- the state machine refuses nonsense ----------


async def test_a_trade_cannot_be_closed_before_it_is_opened(service: TradeService) -> None:
    planned = await service.plan(_plan())
    with pytest.raises(ValidationError):
        await service.close(planned.id, exit_price=Decimal("1.1100"))


async def test_a_cancelled_trade_cannot_be_opened(service: TradeService) -> None:
    planned = await service.plan(_plan())
    await service.cancel(planned.id)
    with pytest.raises(ValidationError):
        await service.open(planned.id, fill_price=Decimal("1.1000"))


async def test_an_unknown_trade_is_rejected(service: TradeService) -> None:
    with pytest.raises(ValidationError):
        await service.open(uuid.uuid4(), fill_price=Decimal("1.1000"))


async def test_free_text_tags_are_refused_before_they_reach_storage() -> None:
    """The API normalises tags before closing; anything outside the taxonomy
    must be rejected rather than silently stored as an uncountable string."""
    with pytest.raises(ValidationError):
        normalise_tags(["i was tired and it felt wrong"])
