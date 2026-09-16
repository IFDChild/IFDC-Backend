import hashlib
import hmac
import os
import secrets
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
)


router = APIRouter(prefix="/api/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)

JWT_SECRET = os.getenv("JWT_SECRET", "change-this-development-secret")
JWT_ALGORITHM = "HS256"
PASSWORD_ITERATIONS = 310_000

# Brute-force protection: too many failed attempts for one email from one
# client blocks further attempts for a short window (in-memory, per process).
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 15 * 60
_failed_attempts: dict[str, deque] = defaultdict(deque)
_attempts_lock = threading.Lock()


def _attempt_key(request: Request, email: str) -> str:
    client = request.client.host if request.client else "unknown"
    return f"{client}:{email}"


def _recent_failures(key: str) -> deque:
    attempts = _failed_attempts[key]
    cutoff = time.monotonic() - LOCKOUT_SECONDS
    while attempts and attempts[0] < cutoff:
        attempts.popleft()
    return attempts


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(candidate.hex(), digest_hex)
    except (TypeError, ValueError):
        return False


def token_lifetime(remember_device: bool) -> timedelta:
    return timedelta(days=30 if remember_device else 1)


def create_access_token(user: User, remember_device: bool) -> str:
    lifetime = token_lifetime(remember_device)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "iat": now,
        "exp": now + lifetime,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive or does not exist",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    key = _attempt_key(request, credentials.email)

    with _attempts_lock:
        failures = _recent_failures(key)
        if len(failures) >= MAX_FAILED_ATTEMPTS:
            retry_after = int(failures[0] + LOCKOUT_SECONDS - time.monotonic()) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Too many failed sign-in attempts. "
                    f"Try again in {max(1, round(retry_after / 60))} minute(s)."
                ),
                headers={"Retry-After": str(retry_after)},
            )

    user = db.query(User).filter(User.email == credentials.email).first()

    if user is None or not verify_password(credentials.password, user.password_hash):
        with _attempts_lock:
            _recent_failures(key).append(time.monotonic())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Contact a system administrator.",
        )

    with _attempts_lock:
        _failed_attempts.pop(key, None)

    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(user, credentials.remember_device),
        expires_in=int(token_lifetime(credentials.remember_device).total_seconds()),
        user=user,
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password",
        )

    current_user.password_hash = hash_password(payload.new_password)
    db.commit()


def seed_admin(db: Session) -> None:
    email = os.getenv("ADMIN_EMAIL", "admin@ifdchild.org").lower()
    password = os.getenv("ADMIN_PASSWORD", "SuperSecureChildPass2024!")

    if db.query(User).filter(User.email == email).first() is None:
        db.add(
            User(
                email=email,
                full_name="IFDC Administrator",
                role="System Administrator",
                password_hash=hash_password(password),
            )
        )
        db.commit()