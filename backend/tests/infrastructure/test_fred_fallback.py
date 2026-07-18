"""FRED adapter: when httpx is blocked by the WAF, the curl fallback runs."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest

from mentor.infrastructure.adapters.macro.fred import (
    FredAdapter,
    FredError,
    MacroObservation,
    _parse_csv,
)


class _BlockedClient:
    """Mimics FRED's WAF: every request dies with a protocol error."""

    async def get(self, *args: object, **kwargs: object) -> httpx.Response:
        raise httpx.RemoteProtocolError("StreamReset")

    async def aclose(self) -> None:  # pragma: no cover - interface parity
        pass


async def test_blocked_httpx_falls_back_to_curl(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = FredAdapter(series_ids=("DGS10",), client=_BlockedClient())  # type: ignore[arg-type]

    called: dict[str, object] = {}

    async def fake_curl(series_id: str, params: dict[str, str]) -> list[MacroObservation]:
        called["series"] = series_id
        called["params"] = params
        return _parse_csv(series_id, "observation_date,DGS10\n2026-01-02,4.25\n")

    monkeypatch.setattr(adapter, "_fetch_via_curl", fake_curl)
    obs = await adapter._fetch_one(
        "DGS10", start=datetime(2026, 1, 1, tzinfo=UTC), end=datetime(2026, 1, 5, tzinfo=UTC)
    )
    assert called["series"] == "DGS10"
    assert len(obs) == 1 and obs[0].value == 4.25


async def test_missing_curl_binary_raises_frederror(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = FredAdapter(series_ids=("DGS10",), client=_BlockedClient())  # type: ignore[arg-type]

    async def no_curl(*args: object, **kwargs: object) -> object:
        raise FileNotFoundError("curl")

    monkeypatch.setattr("asyncio.create_subprocess_exec", no_curl)
    with pytest.raises(FredError, match="curl is unavailable"):
        await adapter._fetch_one(
            "DGS10",
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 5, tzinfo=UTC),
        )
