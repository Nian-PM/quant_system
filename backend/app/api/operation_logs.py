from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.database import SessionDep
from app.core.security import get_current_user
from app.models import User
from app.services.operation_log import list_recent_operations

router = APIRouter(prefix="/operation-logs", tags=["operation logs"])


class OperationLogResponse(BaseModel):
    id: int
    actor: str
    action: str
    target_type: str
    target_id: str
    detail: dict
    created_at: datetime


@router.get("", response_model=list[OperationLogResponse])
def list_operation_logs(
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> list[OperationLogResponse]:
    return [
        OperationLogResponse(
            id=log.id or 0,
            actor=log.actor,
            action=log.action,
            target_type=log.target_type,
            target_id=log.target_id,
            detail=log.detail,
            created_at=log.created_at,
        )
        for log in list_recent_operations(session)
    ]
