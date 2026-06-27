"""Smoke tests for the v1 risk endpoints."""

from __future__ import annotations

from decimal import Decimal

from httpx import AsyncClient


async def test_position_size_eurusd_long(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/risk/position-size",
        json={
            "symbol": "EURUSD",
            "account": {"amount": "10000", "currency": "USD"},
            "risk_percent": "1",
            "direction": "long",
            "entry": "1.08500",
            "stop": "1.08200",
            "target": "1.09100",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "EURUSD"
    # Compare numerically — Decimal serialises as "30.0", which is equal to 30.
    assert Decimal(body["pip_distance"]) == Decimal("30")
    assert Decimal(body["risk_reward_ratio"]) == Decimal("2")


async def test_position_size_validation_error(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/risk/position-size",
        json={
            "symbol": "EURUSD",
            "account": {"amount": "10000", "currency": "USD"},
            "risk_percent": "1",
            "direction": "long",
            "entry": "1.085",
            "stop": "1.085",
        },
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "validation_error"


async def test_expectancy_positive(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/risk/expectancy",
        json={"win_rate_percent": "40", "avg_win_r": "2", "avg_loss_r": "1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_positive"] is True
    assert "edge" in body["interpretation"].lower()


async def test_guardrail_blocks_oversized_trade(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/risk/guardrails",
        json={
            "account": {"amount": "10000", "currency": "USD"},
            "max_risk_per_trade_percent": "2",
            "max_open_risk_percent": "6",
            "daily_loss_limit_percent": "4",
            "prospective_trade_risk": {"amount": "500", "currency": "USD"},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is False
    kinds = {b["kind"] for b in body["breaches"]}
    assert "per_trade" in kinds


async def test_list_instruments(client: AsyncClient) -> None:
    response = await client.get("/api/v1/risk/instruments")
    assert response.status_code == 200
    symbols = {row["symbol"] for row in response.json()}
    assert "EURUSD" in symbols


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
