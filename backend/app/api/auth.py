"""Authentication router: register (client/saloon), login, me."""

from __future__ import annotations

from datetime import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.core.db import get_session
from app.core.security import create_access_token
from app.models.auth import (
    LoginRequest,
    MeResponse,
    RegisterClient,
    RegisterSalon,
    TokenResponse,
    UserRead,
)
from app.models.tables import Salon, SalonAvailability, User
from app.services import auth as auth_svc

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _salon_id_for(session: Session, user: User) -> int | None:
    if user.role != "saloon":
        return None
    salon = session.exec(select(Salon).where(Salon.owner_id == user.id)).first()
    return salon.id if salon else None


@router.post("/register/client", response_model=TokenResponse)
def register_client(
    payload: RegisterClient, session: Session = Depends(get_session)
) -> TokenResponse:
    try:
        user = auth_svc.register_user(
            session,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            role="client",
            phone=payload.phone,
        )
    except auth_svc.AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    assert user.id is not None
    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.post("/register/saloon", response_model=TokenResponse)
def register_saloon(
    payload: RegisterSalon, session: Session = Depends(get_session)
) -> TokenResponse:
    try:
        user = auth_svc.register_user(
            session,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            role="saloon",
        )
    except auth_svc.AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    assert user.id is not None
    salon = Salon(owner_id=user.id, **payload.salon.model_dump())
    session.add(salon)
    session.commit()
    session.refresh(salon)
    # Sensible default opening hours (Mon–Fri 9–5); editable later.
    for day in range(5):
        session.add(
            SalonAvailability(
                salon_id=salon.id, day_of_week=day, start_time=time(9, 0), end_time=time(17, 0)
            )
        )
    session.commit()

    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token, user=UserRead.model_validate(user), salon_id=salon.id)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_session)) -> TokenResponse:
    try:
        user = auth_svc.authenticate(session, payload.email, payload.password)
    except auth_svc.AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    assert user.id is not None
    token = create_access_token(user.id, user.role)
    return TokenResponse(
        access_token=token,
        user=UserRead.model_validate(user),
        salon_id=_salon_id_for(session, user),
    )


@router.get("/me", response_model=MeResponse)
def me(
    user: User = Depends(get_current_user), session: Session = Depends(get_session)
) -> MeResponse:
    return MeResponse(user=UserRead.model_validate(user), salon_id=_salon_id_for(session, user))
