from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import select

from app.core.database import SessionDep
from app.core.security import get_current_user
from app.models import BacktestRun, Bar, Instrument, StrategyParameterSet, TaskStatus, User
from app.services.backtest import run_single_instrument_backtest
from app.services.operation_log import record_operation

router = APIRouter(prefix="/backtests", tags=["backtests"])


class BacktestCreate(BaseModel):
    instrument_id: int
    frequency: str = "5m"
    parameter_set_id: int
    initial_cash: float = Field(default=100000, gt=0)


class BacktestRunResponse(BaseModel):
    id: int
    strategy_id: str
    parameter_set_id: int | None
    status: TaskStatus
    config: dict
    metrics: dict
    result_payload: dict
    message: str
    created_at: datetime


def backtest_response(backtest: BacktestRun) -> BacktestRunResponse:
    return BacktestRunResponse(
        id=backtest.id or 0,
        strategy_id=backtest.strategy_id,
        parameter_set_id=backtest.parameter_set_id,
        status=backtest.status,
        config=backtest.config,
        metrics=backtest.metrics,
        result_payload=backtest.result_payload,
        message=backtest.message,
        created_at=backtest.created_at,
    )


@router.get("", response_model=list[BacktestRunResponse])
def list_backtests(
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> list[BacktestRunResponse]:
    statement = select(BacktestRun).order_by(BacktestRun.created_at.desc())
    return [backtest_response(backtest) for backtest in session.exec(statement).all()]


@router.post("", response_model=BacktestRunResponse)
def create_backtest(
    payload: BacktestCreate,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> BacktestRunResponse:
    instrument = session.get(Instrument, payload.instrument_id)
    if not instrument:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown instrument id: {payload.instrument_id}",
        )

    parameter_set = session.get(StrategyParameterSet, payload.parameter_set_id)
    if not parameter_set:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown parameter set id: {payload.parameter_set_id}",
        )

    frequency = payload.frequency.strip().lower()
    statement = (
        select(Bar)
        .where(Bar.instrument_id == payload.instrument_id, Bar.frequency == frequency)
        .order_by(Bar.timestamp)
    )
    bars = session.exec(statement).all()

    try:
        result = run_single_instrument_backtest(
            bars=bars,
            parameter_set=parameter_set,
            initial_cash=payload.initial_cash,
        )
    except ValueError as exc:
        record_operation(
            session,
            action="backtest.create.failed",
            actor=current_user.username,
            target_type="instrument",
            target_id=str(payload.instrument_id),
            detail={"message": str(exc), "frequency": frequency},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    backtest = BacktestRun(
        strategy_id=parameter_set.strategy_id,
        parameter_set_id=parameter_set.id,
        status=TaskStatus.succeeded,
        config={
            "instrument_id": payload.instrument_id,
            "frequency": frequency,
            "initial_cash": payload.initial_cash,
        },
        metrics=result.metrics,
        result_payload=result.result_payload,
        message="Backtest succeeded",
    )
    session.add(backtest)
    session.commit()
    session.refresh(backtest)

    record_operation(
        session,
        action="backtest.create.succeeded",
        actor=current_user.username,
        target_type="backtest_run",
        target_id=str(backtest.id),
        detail={"instrument_id": payload.instrument_id, "frequency": frequency},
    )
    return backtest_response(backtest)
