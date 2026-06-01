from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import select

from app.core.database import SessionDep
from app.core.security import get_current_user
from app.models import StrategyParameterSet, User
from app.services.operation_log import record_operation
from app.strategies.registry import normalize_strategy_parameters

router = APIRouter(prefix="/strategy-parameter-sets", tags=["strategy-parameter-sets"])


class StrategyParameterSetCreate(BaseModel):
    strategy_id: str
    name: str = Field(min_length=1)
    parameters: dict = Field(default_factory=dict)


class StrategyParameterSetResponse(BaseModel):
    id: int
    strategy_id: str
    name: str
    parameters: dict
    created_at: datetime


def parameter_set_response(parameter_set: StrategyParameterSet) -> StrategyParameterSetResponse:
    return StrategyParameterSetResponse(
        id=parameter_set.id or 0,
        strategy_id=parameter_set.strategy_id,
        name=parameter_set.name,
        parameters=parameter_set.parameters,
        created_at=parameter_set.created_at,
    )


@router.get("", response_model=list[StrategyParameterSetResponse])
def list_strategy_parameter_sets(
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> list[StrategyParameterSetResponse]:
    statement = select(StrategyParameterSet).order_by(StrategyParameterSet.created_at.desc())
    return [parameter_set_response(item) for item in session.exec(statement).all()]


@router.post("", response_model=StrategyParameterSetResponse)
def create_strategy_parameter_set(
    payload: StrategyParameterSetCreate,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> StrategyParameterSetResponse:
    strategy_id = payload.strategy_id.strip()
    try:
        normalized_parameters = normalize_strategy_parameters(strategy_id, payload.parameters)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    parameter_set = StrategyParameterSet(
        strategy_id=strategy_id,
        name=payload.name.strip(),
        parameters=normalized_parameters,
    )
    session.add(parameter_set)
    session.commit()
    session.refresh(parameter_set)

    record_operation(
        session,
        action="strategy_parameter_set.create",
        actor=current_user.username,
        target_type="strategy_parameter_set",
        target_id=str(parameter_set.id),
        detail={"strategy_id": strategy_id, "name": parameter_set.name},
    )
    return parameter_set_response(parameter_set)
