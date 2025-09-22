"""Helpers for managing the virtual scheduler user account."""

import secrets
from sqlalchemy.orm import Session

from models import User, UserRole
from scheduler_config import SCHEDULER_USERNAME


def ensure_scheduler_user(db: Session) -> User:
    """Return the scheduler user, creating it with a strong random password if missing."""
    user = db.query(User).filter(User.username == SCHEDULER_USERNAME).first()
    if user:
        return user

    from auth import get_password_hash  # Imported lazily to avoid circular dependency

    random_secret = secrets.token_urlsafe(64)
    user = User(
        username=SCHEDULER_USERNAME,
        password_hash=get_password_hash(random_secret),
        role=UserRole.MAINTAINER,
        email=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
