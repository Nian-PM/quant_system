from fastapi import APIRouter
from sqlmodel import select

from app.core.database import engine
from app.core.database import SessionDep
from app.models import Instrument
from app.services.schema import check_database_schema

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(session: SessionDep) -> dict[str, object]:
    instrument_count = len(session.exec(select(Instrument.id)).all())
    schema_report = check_database_schema(engine)
    return {
        "status": "ok" if schema_report.status == "ok" else "degraded",
        "database": "ok",
        "schema": {
            "status": schema_report.status,
            "missing_tables": schema_report.missing_tables,
            "missing_columns": schema_report.missing_columns,
        },
        "instrument_count": instrument_count,
    }
