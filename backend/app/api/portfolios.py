from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.core.database import SessionDep
from app.core.security import get_current_user
from app.models import Instrument, Portfolio, PortfolioInstrument, User
from app.services.operation_log import record_operation

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


class PortfolioPositionCreate(BaseModel):
    instrument_id: int
    weight: float = Field(gt=0)


class PortfolioCreate(BaseModel):
    name: str
    description: str = ""
    positions: list[PortfolioPositionCreate] = Field(default_factory=list)


class InstrumentSummary(BaseModel):
    id: int
    symbol: str
    exchange: str
    name: str
    asset_type: str


class PortfolioPositionResponse(BaseModel):
    instrument: InstrumentSummary
    weight: float


class PortfolioResponse(BaseModel):
    id: int
    name: str
    description: str
    positions: list[PortfolioPositionResponse]
    created_at: datetime


def instrument_summary(instrument: Instrument) -> InstrumentSummary:
    return InstrumentSummary(
        id=instrument.id or 0,
        symbol=instrument.symbol,
        exchange=instrument.exchange,
        name=instrument.name,
        asset_type=instrument.asset_type,
    )


def portfolio_response(session: Session, portfolio: Portfolio) -> PortfolioResponse:
    statement = select(PortfolioInstrument).where(PortfolioInstrument.portfolio_id == portfolio.id)
    rows = session.exec(statement).all()
    positions: list[PortfolioPositionResponse] = []

    for row in rows:
        instrument = session.get(Instrument, row.instrument_id)
        if instrument:
            positions.append(
                PortfolioPositionResponse(
                    instrument=instrument_summary(instrument),
                    weight=row.weight,
                )
            )

    return PortfolioResponse(
        id=portfolio.id or 0,
        name=portfolio.name,
        description=portfolio.description,
        positions=positions,
        created_at=portfolio.created_at,
    )


@router.get("", response_model=list[PortfolioResponse])
def list_portfolios(
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> list[PortfolioResponse]:
    statement = select(Portfolio).order_by(Portfolio.created_at.desc())
    return [portfolio_response(session, portfolio) for portfolio in session.exec(statement).all()]


@router.post("", response_model=PortfolioResponse)
def create_portfolio(
    payload: PortfolioCreate,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> PortfolioResponse:
    portfolio = Portfolio(name=payload.name.strip(), description=payload.description.strip())
    session.add(portfolio)
    session.commit()
    session.refresh(portfolio)

    for position in payload.positions:
        instrument = session.get(Instrument, position.instrument_id)
        if not instrument:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown instrument id: {position.instrument_id}",
            )
        session.add(
            PortfolioInstrument(
                portfolio_id=portfolio.id or 0,
                instrument_id=position.instrument_id,
                weight=position.weight,
            )
        )

    session.commit()

    record_operation(
        session,
        action="portfolio.create",
        actor=current_user.username,
        target_type="portfolio",
        target_id=str(portfolio.id),
        detail={"name": portfolio.name, "positions": len(payload.positions)},
    )
    return portfolio_response(session, portfolio)
