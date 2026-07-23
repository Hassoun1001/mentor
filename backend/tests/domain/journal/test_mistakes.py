"""Loss root causes: a closed taxonomy, ranked by damage not frequency."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.journal.mistakes import (
    MistakeTag,
    compute_root_causes,
    mistake_catalog,
    normalise_tags,
)
from mentor.domain.journal.trade import Trade, TradeStatus
from mentor.domain.money import Money
from mentor.domain.risk.position_sizing import Direction


def _closed(r: str, tags: tuple[str, ...]) -> Trade:
    return Trade(
        id=uuid.uuid4(),
        symbol="EURUSD",
        direction=Direction.LONG,
        status=TradeStatus.CLOSED,
        size_lots=Decimal("0.1"),
        planned_entry=Decimal("1.1000"),
        planned_stop=Decimal("1.0950"),
        planned_target=Decimal("1.1100"),
        initial_risk=Money(Decimal("100"), "USD"),
        reason="test",
        realised_r=Decimal(r),
        mistake_tags=tags,
    )


# ---------- taxonomy ----------


def test_every_tag_has_a_definition_with_a_question_and_a_fix() -> None:
    catalog = mistake_catalog()
    assert {d.tag for d in catalog} == set(MistakeTag)
    for d in catalog:
        assert d.question.strip() and d.fix.strip()


def test_good_process_is_not_a_process_error() -> None:
    errors = {d.tag for d in mistake_catalog() if d.is_process_error}
    assert MistakeTag.GOOD_PROCESS not in errors
    assert MistakeTag.MOVED_STOP in errors


# ---------- normalisation ----------


def test_normalise_accepts_hyphens_and_case_and_dedupes() -> None:
    assert normalise_tags(["False-Breakout", "false_breakout", " NEWS SHOCK "]) == (
        "false_breakout",
        "news_shock",
    )


def test_normalise_rejects_free_text() -> None:
    with pytest.raises(ValidationError):
        normalise_tags(["i was tired"])


def test_normalise_skips_blanks() -> None:
    assert normalise_tags(["", "  ", "oversized"]) == ("oversized",)


# ---------- breakdown ----------


def test_only_losses_are_diagnosed() -> None:
    b = compute_root_causes([_closed("2.0", ("oversized",)), _closed("-1.0", ("oversized",))])
    assert b.closed_losses == 1
    assert b.causes[0].occurrences == 1


def test_ranking_is_by_r_bled_not_by_count() -> None:
    trades = [
        _closed("-0.2", ("bad_timing",)),
        _closed("-0.2", ("bad_timing",)),
        _closed("-0.2", ("bad_timing",)),
        _closed("-3.0", ("oversized",)),  # one trade, far more damage
    ]
    b = compute_root_causes(trades)
    assert b.worst is not None
    assert b.worst.tag is MistakeTag.OVERSIZED
    assert b.worst.r_lost == Decimal("3.0")
    assert b.causes[1].occurrences == 3


def test_a_multi_tag_loss_attributes_full_r_to_each_cause() -> None:
    b = compute_root_causes([_closed("-1.5", ("revenge_trade", "oversized"))])
    assert {c.r_lost for c in b.causes} == {Decimal("1.5")}
    assert b.tagged_losses == 1


def test_untagged_losses_are_counted_not_hidden() -> None:
    b = compute_root_causes([_closed("-1.0", ()), _closed("-1.0", ("no_setup",))])
    assert (b.tagged_losses, b.untagged_losses) == (1, 1)


def test_good_process_losses_are_separated_from_mistakes() -> None:
    b = compute_root_causes([_closed("-1.0", ("good_process",)), _closed("-1.0", ("moved_stop",))])
    assert b.good_process_losses == 1
    assert b.process_error_losses == 1


def test_legacy_free_text_tags_never_crash_the_review() -> None:
    b = compute_root_causes([_closed("-1.0", ("bad entry vibes",))])
    assert b.closed_losses == 1
    assert b.tagged_losses == 0
    assert b.causes == ()


def test_empty_journal_is_empty_not_an_error() -> None:
    b = compute_root_causes([])
    assert b.closed_losses == 0
    assert b.worst is None
