from fastapi import APIRouter
from sqlmodel import select

from app.core.database import SessionDep
from app.models import Instrument

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(session: SessionDep) -> dict[str, object]:
    instrument_count = len(session.exec(select(Instrument.id)).all())
    return {
        "status": "ok",
        "database": "ok",
        "instrument_count": instrument_count,
    }
