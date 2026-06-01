from fastapi import APIRouter

from app.strategies.registry import get_strategy_registry

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("")
def list_strategies() -> list[dict]:
    return [strategy.model_dump() for strategy in get_strategy_registry()]
