import jwt

from datetime import datetime, timedelta
from fastapi import Header, HTTPException, status
from typing import Optional


JWT_KEY = "aowidhv9291o4hliawd"
JWT_ALGO = "HS256"


def jwt_encode(data: dict, exp_hours: Optional[int]) -> str:
    data = data.copy()
    if exp_hours:
        data["exp"] = datetime.now() + timedelta(hours=exp_hours)
    return jwt.encode(data, JWT_KEY, JWT_ALGO)


def jwt_verify(token: str = Header(None, alias="Access-Token")) -> dict:
    try:
        if token is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
        return jwt.decode(token, JWT_KEY, JWT_ALGO)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
