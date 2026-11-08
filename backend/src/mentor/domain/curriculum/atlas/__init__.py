"""The Methods Atlas: one card for each of 150 named trading methods, grouped A to I."""

from __future__ import annotations

from typing import Final

from mentor.domain.curriculum.atlas.group_a_technical import GROUP_A
from mentor.domain.curriculum.atlas.group_b_structure import GROUP_B
from mentor.domain.curriculum.atlas.group_c_flow import GROUP_C
from mentor.domain.curriculum.atlas.group_d_indicators import GROUP_D
from mentor.domain.curriculum.atlas.group_e_macro import GROUP_E
from mentor.domain.curriculum.atlas.group_f_quant import GROUP_F
from mentor.domain.curriculum.atlas.group_g_options import GROUP_G
from mentor.domain.curriculum.atlas.group_h_sentiment import GROUP_H
from mentor.domain.curriculum.atlas.group_i_risk import GROUP_I
from mentor.domain.curriculum.atlas.model import Access, Group, Market, Method, Trader, Usage

ATLAS: Final[tuple[Group, ...]] = (
    GROUP_A,
    GROUP_B,
    GROUP_C,
    GROUP_D,
    GROUP_E,
    GROUP_F,
    GROUP_G,
    GROUP_H,
    GROUP_I,
)

USAGE_NOTE: Final[str] = (
    "Nobody counts how many traders use each method, so no real census exists. "
    "The usage labels here are informed judgements. We based them on surveys where they "
    "exist, on what trading platforms and courses offer, and on published research. "
    "They are not measured percentages. Popularity and evidence are separate labels: "
    "a very popular method can still have weak evidence."
)

__all__ = ["ATLAS", "USAGE_NOTE", "Access", "Group", "Market", "Method", "Trader", "Usage"]
