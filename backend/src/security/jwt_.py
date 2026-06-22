import hashlib

from typing import Optional
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer
from jose import jwt


from shared.config.config import config

SECRET_KEY = config.JWT_SECRET_KEY
ALGORITHM = config.JWT_ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    pre_hashed = hashlib.sha256(password.encode("utf-8")).hexdigest()

    return pwd_context.hash(pre_hashed)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    pre_hashed = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()

    return pwd_context.verify(pre_hashed, hashed_password)


ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)

    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + timedelta(minutes=15)

    to_encode.update({"exp": int(expire.timestamp())})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
