from sqlmodel import Session, select

from app.models import OperationLog


def record_operation(
    session: Session,
    action: str,
    actor: str = "system",
    target_type: str = "",
    target_id: str = "",
    detail: dict | None = None,
) -> OperationLog:
    log = OperationLog(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail or {},
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


def list_recent_operations(session: Session, limit: int = 100) -> list[OperationLog]:
    statement = select(OperationLog).order_by(OperationLog.created_at.desc()).limit(limit)
    return list(session.exec(statement).all())
