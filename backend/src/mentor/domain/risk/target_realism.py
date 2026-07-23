"""Is this target actually reachable before the trade expires?

The plan sets a stop from volatility (1.5 sigma) and then a target at some
reward multiple of it. At the default 2:1 that puts the target **three
sigma** away — and the time stop closes the trade at the end of the very
horizon that sigma was measured over. So the ticket advertises a 2:1 trade
that, most of the time, can only end at the time stop.

Two facts make this concrete, and neither is intuitive.

**Reward:risk does not create edge.** For a driftless walk with barriers at
``-s`` and ``+t``, the chance of touching the target first is ``s/(s+t)``.
At 2:1 that is exactly one in three — precisely the win rate needed to
break even at 2:1. Widening the target lowers the hit rate by the same
proportion it raises the payoff. Every "just use 3:1 reward-to-risk" course
is selling arithmetic that cancels. Only a directional edge — being right
more often than the barrier ratio implies — makes money.

**A distant target and a time stop fight each other.** The barrier ratio
above assumes you wait forever. With a time stop at the horizon, paths that
would eventually have reached the target are cut short, so the realised
target-hit rate is *lower* than ``s/(s+t)`` and the expiry rate is high.
The further out the target, the more the trade is really a bet on the time
stop.

So the plan states the break-even win rate next to the model's actual
measured accuracy. If the model cannot clear the bar its own reward
multiple sets, the ticket says so before money is committed.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from mentor.domain.errors import ValidationError


@dataclass(frozen=True, slots=True)
class TargetRealism:
    stop_sigma: Decimal  # stop distance in expected-move sigmas
    target_sigma: Decimal  # target distance in expected-move sigmas
    reward_risk: Decimal
    breakeven_win_rate: Decimal  # 1 / (1 + R)
    random_walk_hit_rate: Decimal  # s / (s + t) — no-edge baseline
    model_win_rate: Decimal | None  # the model's own measured accuracy
    has_edge: bool | None  # None when the model's accuracy is unknown
    note: str


def assess_target(
    *,
    stop_pips: Decimal,
    target_pips: Decimal,
    expected_move_pips: Decimal,
    model_win_rate: Decimal | None = None,
) -> TargetRealism:
    """Compare the target's distance and payoff with what it demands.

    ``expected_move_pips`` is the 1-sigma move over the same horizon the
    trade is held for, so the sigma multiples below are directly comparable
    with the time stop.
    """
    if stop_pips <= 0:
        raise ValidationError("stop_pips must be positive", field="stop_pips")
    if target_pips <= 0:
        raise ValidationError("target_pips must be positive", field="target_pips")

    reward_risk = target_pips / stop_pips
    breakeven = Decimal("1") / (Decimal("1") + reward_risk)
    rw_hit = stop_pips / (stop_pips + target_pips)  # identical to breakeven

    sigma = expected_move_pips
    stop_sigma = (stop_pips / sigma) if sigma > 0 else Decimal("0")
    target_sigma = (target_pips / sigma) if sigma > 0 else Decimal("0")

    has_edge: bool | None = None
    if model_win_rate is not None:
        has_edge = model_win_rate > breakeven

    parts: list[str] = [
        f"At {reward_risk:.1f}:1 you need to win {breakeven * 100:.0f}% of these "
        f"trades just to break even."
    ]

    if sigma > 0:
        parts.append(
            f"The target sits {target_sigma:.1f} sigma away and the trade is closed "
            f"at the time stop after one horizon — the same horizon that sigma was "
            f"measured over."
        )
        if target_sigma >= Decimal("2"):
            parts.append(
                "A move that large inside one horizon is uncommon, so most of these "
                "trades will end at the time stop rather than at the target. The "
                "advertised reward is mostly theoretical."
            )

    if model_win_rate is None:
        parts.append(
            "No measured accuracy for the model in charge, so whether it clears that "
            "bar is unknown — which is itself a reason for caution."
        )
    elif has_edge:
        parts.append(
            f"The model's measured accuracy is {model_win_rate * 100:.0f}%, above the "
            f"{breakeven * 100:.0f}% needed. Thin, but the right side of the line."
        )
    else:
        parts.append(
            f"The model's measured accuracy is {model_win_rate * 100:.0f}%, at or below "
            f"the {breakeven * 100:.0f}% this reward multiple demands. On these numbers "
            f"the trade has no expected edge — raising the target does not fix that, "
            f"because it lowers the hit rate by the same proportion."
        )

    return TargetRealism(
        stop_sigma=stop_sigma.quantize(Decimal("0.01")),
        target_sigma=target_sigma.quantize(Decimal("0.01")),
        reward_risk=reward_risk.quantize(Decimal("0.01")),
        breakeven_win_rate=breakeven.quantize(Decimal("0.0001")),
        random_walk_hit_rate=rw_hit.quantize(Decimal("0.0001")),
        model_win_rate=model_win_rate,
        has_edge=has_edge,
        note=" ".join(parts),
    )
