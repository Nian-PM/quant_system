from fastapi import APIRouter

from app.api import auth, health, instruments, market_data, operation_logs, portfolios, strategies

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(health.router)
api_router.include_router(instruments.router)
api_router.include_router(market_data.router)
api_router.include_router(operation_logs.router)
api_router.include_router(portfolios.router)
api_router.include_router(strategies.router)
