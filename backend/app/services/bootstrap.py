from sqlmodel import Session

from app.core.config import get_settings
from app.core.security import find_user_by_username, hash_password
from app.models import User
from app.services.operation_log import record_operation


def seed_default_admin(session: Session) -> None:
    settings = get_settings()
    if find_user_by_username(session, settings.admin_username):
        return

    user = User(
        username=settings.admin_username,
        password_hash=hash_password(settings.admin_password),
    )
    session.add(user)
    session.commit()
    record_operation(
        session,
        action="auth.admin.seeded",
        actor="system",
        target_type="user",
        target_id=settings.admin_username,
    )
