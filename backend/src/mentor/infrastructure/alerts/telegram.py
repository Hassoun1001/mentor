"""Telegram notifier — the loop's voice.

A 24/7 loop knows interesting things at 3am: a high-confidence signal,
a drift retrain, a promoted model, a dying data feed. A dashboard nobody
is watching can't tell you; a Telegram message can.

Setup (free, ~2 minutes): message @BotFather → /newbot → copy the token
into TELEGRAM_BOT_TOKEN; message your new bot once, then GET
https://api.telegram.org/bot<token>/getUpdates and copy your chat id
into MENTOR_TELEGRAM_CHAT_ID. Unset means disabled — the notifier is a
silent no-op, never a crash: alerting must never take down the loop.
"""

from __future__ import annotations

import httpx

from mentor.config import Settings
from mentor.logging import get_logger

log = get_logger("mentor.alerts.telegram")

_API = "https://api.telegram.org"
_TIMEOUT = httpx.Timeout(10.0)


class TelegramNotifier:
    def __init__(self, *, token: str, chat_id: str) -> None:
        self._token = token.strip()
        self._chat_id = chat_id.strip()

    @property
    def enabled(self) -> bool:
        return bool(self._token and self._chat_id)

    async def send(self, text: str) -> bool:
        """Deliver `text`; returns True on success. Never raises."""
        if not self.enabled:
            return False
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(
                    f"{_API}/bot{self._token}/sendMessage",
                    json={"chat_id": self._chat_id, "text": text},
                )
            if resp.status_code != 200:
                log.warning("telegram.send_failed", status=resp.status_code)
                return False
            return True
        except httpx.HTTPError as exc:
            log.warning("telegram.send_failed", error=str(exc))
            return False


def build_notifier(settings: Settings) -> TelegramNotifier:
    return TelegramNotifier(
        token=settings.telegram_bot_token.get_secret_value(),
        chat_id=settings.telegram_chat_id,
    )
