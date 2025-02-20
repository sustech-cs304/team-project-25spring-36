import jwt

from datetime import datetime, timedelta
from fastapi import Header, HTTPException, status


JWT_KEY = "aowidhv9291o4hliawd"
JWT_ALGO = "HS256"


def jwt_encode(data: dict) -> str:
    return jwt.encode({**data, "exp": datetime.now() + timedelta(hours=24)}, JWT_KEY, JWT_ALGO)


def jwt_verify(token: str = Header(None, alias="Access-Token")) -> dict:
    try:
        if token is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
        return jwt.decode(token, JWT_KEY, JWT_ALGO)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
