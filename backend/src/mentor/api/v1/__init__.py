"""API v1 routers."""

from fastapi import APIRouter

from mentor.api.v1 import (
    alerts,
    auth,
    backtest,
    calendar,
    curriculum,
    explain,
    forecasting,
    health,
    journal,
    news,
    prices,
    risk,
    risk_simulator,
    trades,
)

api_v1 = APIRouter()
api_v1.include_router(health.router)
api_v1.include_router(auth.router)
api_v1.include_router(risk.router)
api_v1.include_router(risk_simulator.router)
api_v1.include_router(trades.router)
api_v1.include_router(journal.router)
api_v1.include_router(prices.router)
api_v1.include_router(curriculum.router)
api_v1.include_router(explain.router)
api_v1.include_router(backtest.router)
api_v1.include_router(forecasting.router)
api_v1.include_router(news.router)
api_v1.include_router(alerts.router)
api_v1.include_router(calendar.router)
