"""Anthropic-backed tip parser.

Turns a raw tipster message into structured `ParsedTip`s. Server-side
only; the key never leaves the backend. Parsing is deliberately tolerant:
unknown categories fall back to OTHER, unknown actions to WATCH, so a
weird message degrades gracefully instead of failing the whole ingest.
"""

from __future__ import annotations

import json
from collections.abc import Sequence

from anthropic import AsyncAnthropic
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from mentor.config import get_settings
from mentor.domain.tips.parser import TipParser
from mentor.domain.tips.tip import Conviction, ParsedTip, TipAction, TipCategory
from mentor.logging import get_logger

log = get_logger("mentor.tips.parser")

_SYSTEM = """You extract stock tips from a tipster's chat message into JSON.

Return ONLY a JSON array (no prose, no code fences). Each element:
{"ticker": "SYMBOL", "category": "safe|high_risk|picks_and_shovels|other",
 "action": "buy|buy_on_dip|hold|watch|avoid", "conviction": "high|medium|low",
 "note": "the tipster's own words for this ticker, brief"}

Rules:
- ticker = the uppercase stock symbol only (strip $).
- category: use the section header the ticker sits under ("Safe bet"->safe,
  "High Risk, High Reward"->high_risk, "Picks and shovels"->picks_and_shovels).
  If none, "other".
- action: "buy"/"buy definitely"/"very cheap so you can buy"->buy;
  "wait for dip"/"is dipping so wait"/"when it dips"/"check a good entry"->buy_on_dip;
  "long hold"/"keep 2-3"->hold; "keep an eye"/just listed->watch; "avoid"/"die-off"->avoid.
- conviction: strong language ("definitely","very important","imp")->high; hedged
  ("could","may","see if")->low; otherwise medium.
- One element per ticker mention. Deduplicate exact repeats, keeping the strongest action."""


def _coerce_category(value: str) -> TipCategory:
    try:
        return TipCategory(value.strip().lower())
    except ValueError:
        return TipCategory.OTHER


def _coerce_action(value: str) -> TipAction:
    try:
        return TipAction(value.strip().lower())
    except ValueError:
        return TipAction.WATCH


def _coerce_conviction(value: str) -> Conviction:
    try:
        return Conviction(value.strip().lower())
    except ValueError:
        return Conviction.MEDIUM


def _extract_json(text: str) -> str:
    body = text.strip()
    if body.startswith("```"):
        body = body.split("```")[1]
        if body.lstrip().lower().startswith("json"):
            body = body.lstrip()[4:]
    return body.strip()


class AnthropicTipParser(TipParser):
    def __init__(self, *, api_key: str, model: str, max_tokens: int = 3000) -> None:
        if not api_key:
            raise ValueError("AnthropicTipParser requires an api_key")
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential_jitter(initial=0.5, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def parse(self, *, text: str) -> Sequence[ParsedTip]:
        message = await self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=_SYSTEM,
            messages=[{"role": "user", "content": text}],
        )
        raw = "".join(getattr(b, "text", "") or "" for b in message.content)
        try:
            data = json.loads(_extract_json(raw))
        except (ValueError, IndexError) as exc:
            log.warning("tips.parse_failed", error=str(exc))
            return []

        tips: list[ParsedTip] = []
        seen: set[str] = set()
        for row in data if isinstance(data, list) else []:
            ticker = str(row.get("ticker", "")).strip().upper().lstrip("$")
            if not ticker or ticker in seen:
                continue
            seen.add(ticker)
            tips.append(
                ParsedTip(
                    ticker=ticker,
                    category=_coerce_category(str(row.get("category", "other"))),
                    action=_coerce_action(str(row.get("action", "watch"))),
                    conviction=_coerce_conviction(str(row.get("conviction", "medium"))),
                    note=str(row.get("note", "")).strip()[:280],
                )
            )
        log.info(
            "tips.parsed",
            count=len(tips),
            model=self._model,
            input_tokens=getattr(message.usage, "input_tokens", None),
            output_tokens=getattr(message.usage, "output_tokens", None),
        )
        return tips


def build_tip_parser() -> AnthropicTipParser:
    """Construct the live parser from settings. Unlike the explainer there
    is no deterministic fallback — parsing arbitrary tipster prose needs the
    model — so the caller must handle the missing-key case."""
    settings = get_settings()
    api_key = settings.anthropic_api_key.get_secret_value().strip()
    if not api_key:
        raise ValueError("tip parsing requires ANTHROPIC_API_KEY")
    return AnthropicTipParser(api_key=api_key, model=settings.llm_model)
