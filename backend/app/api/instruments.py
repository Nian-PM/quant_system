from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import select

from app.core.database import SessionDep
from app.core.security import get_current_user
from app.models import Instrument, User
from app.services.operation_log import record_operation

router = APIRouter(prefix="/instruments", tags=["instruments"])


class InstrumentCreate(BaseModel):
    symbol: str
    exchange: str
    name: str
    asset_type: str = "stock"


class InstrumentResponse(BaseModel):
    id: int
    symbol: str
    exchange: str
    name: str
    asset_type: str
    created_at: datetime


def to_response(instrument: Instrument) -> InstrumentResponse:
    return InstrumentResponse(
        id=instrument.id or 0,
        symbol=instrument.symbol,
        exchange=instrument.exchange,
        name=instrument.name,
        asset_type=instrument.asset_type,
        created_at=instrument.created_at,
    )


@router.get("", response_model=list[InstrumentResponse])
def list_instruments(
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> list[InstrumentResponse]:
    statement = select(Instrument).order_by(Instrument.exchange, Instrument.symbol)
    return [to_response(instrument) for instrument in session.exec(statement).all()]


@router.post("", response_model=InstrumentResponse)
def create_instrument(
    payload: InstrumentCreate,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> InstrumentResponse:
    instrument = Instrument(
        symbol=payload.symbol.strip().upper(),
        exchange=payload.exchange.strip().upper(),
        name=payload.name.strip(),
        asset_type=payload.asset_type.strip().lower(),
    )
    session.add(instrument)
    session.commit()
    session.refresh(instrument)

    record_operation(
        session,
        action="instrument.create",
        actor=current_user.username,
        target_type="instrument",
        target_id=str(instrument.id),
        detail={"symbol": instrument.symbol, "exchange": instrument.exchange},
    )
    return to_response(instrument)
