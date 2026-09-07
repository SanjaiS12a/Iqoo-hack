from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from .models import User

password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)


def hash_password(value: str) -> str:
    return password_hash.hash(value)


def verify_password(value: str, hashed: str) -> bool:
    return password_hash.verify(value, hashed)


def create_token(user: User, secret: str, expire_minutes: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    return jwt.encode({"sub": str(user.id), "role": user.role, "exp": expires}, secret, algorithm="HS256")


def current_user_dependency(get_db, secret: str):
    def current_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
        db: Session = Depends(get_db),
    ) -> User:
        if credentials is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
        try:
            payload = jwt.decode(credentials.credentials, secret, algorithms=["HS256"])
            user_id = int(payload["sub"])
        except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
            raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
        user = db.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="User no longer exists")
        return user

    return current_user


def require_role(role: str, current_user):
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role != role:
            raise HTTPException(status_code=403, detail=f"{role.title()} access required")
        return user

    return dependency
