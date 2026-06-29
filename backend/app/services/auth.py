"""User registration and authentication."""

from __future__ import annotations

from sqlmodel import Session, select

from app.core.security import hash_password, verify_password
from app.models.tables import User


class AuthError(Exception):
    """Raised on registration/authentication failures."""


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()


def register_user(
    session: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    role: str,
    phone: str | None = None,
) -> User:
    if role not in ("client", "saloon"):
        raise AuthError("Invalid role.")
    if get_user_by_email(session, email) is not None:
        raise AuthError("An account with that email already exists.")
    user = User(
        email=email.strip().lower(),
        hashed_password=hash_password(password),
        full_name=full_name.strip(),
        role=role,
        phone=phone,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate(session: Session, email: str, password: str) -> User:
    user = get_user_by_email(session, email.strip().lower())
    if user is None or not verify_password(password, user.hashed_password):
        raise AuthError("Incorrect email or password.")
    return user
