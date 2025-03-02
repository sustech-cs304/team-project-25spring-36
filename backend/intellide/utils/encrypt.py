from datetime import datetime, timedelta
from typing import Optional, Dict

import jwt
from fastapi import Header, HTTPException, status

from intellide.config import ENCRYPT_JWT_ALGO, ENCRYPT_KEY


def jwt_encode(
        data: Dict,
        exp_hours: Optional[int],
) -> str:
    """
    生成 JWT

    参数:
    - data: 包含要编码的数据的字典
    - exp_hours: 过期时间（小时），可选

    返回:
    - 生成的 JWT 字符串
    """
    data = data.copy()
    if exp_hours:
        data["exp"] = datetime.now() + timedelta(hours=exp_hours)
    return jwt.encode(data, ENCRYPT_KEY, ENCRYPT_JWT_ALGO)


def jwt_decode(
        token: str = Header(None, alias="Access-Token"),
) -> Dict:
    """
    验证 JWT

    参数:
    - token: 要验证的 JWT 字符串，从请求头中获取

    返回:
    - 解码后的数据字典

    抛出:
    - HTTPException: 如果 token 缺失或无效
    """
    try:
        if token is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
        return jwt.decode(token, ENCRYPT_KEY, ENCRYPT_JWT_ALGO)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
