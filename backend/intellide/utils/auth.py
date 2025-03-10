import base64
import binascii
import json
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict

from fastapi import Header, HTTPException, status
from jwcrypto import jwk, jwe
from jwcrypto.common import json_encode

from intellide.config import AUTH_JWE_ALG, AUTH_JWE_ENC

_jwe_key = jwk.JWK.generate(kty='oct', size=256)


def jwe_encode(
        data: Dict,
        exp_hours: Optional[int],
) -> str:
    """
    生成 JWT

    参数:
    - data: 包含要编码的数据的字典
    - exp_hours: 过期时间（小时），可选

    返回:
    - 生成的 JWE 字符串
    """
    data = data.copy()
    if exp_hours:
        data["exp"] = (datetime.now() + timedelta(hours=exp_hours)).timestamp()
    cipher = jwe.JWE(
        json.dumps(data).encode("utf-8"),
        json_encode(
            {
                "alg": AUTH_JWE_ALG,
                "enc": AUTH_JWE_ENC,
            }
        ),
    )
    cipher.add_recipient(_jwe_key)
    return base64.b64encode(cipher.serialize(compact=True).encode("utf-8")).decode("utf-8")


def jwe_decode(
        token: str = Header(None, alias="Access-Token"),
) -> Dict:
    """
    验证 JWT

    参数:
    - token: 要验证的 JWE 字符串，从请求头中获取

    返回:
    - 解码后的数据字典

    抛出:
    - HTTPException: 如果 token 缺失或无效
    """
    try:
        if token is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
        token = base64.b64decode(token).decode("utf-8")
        cipher = jwe.JWE()
        cipher.deserialize(token)
        cipher.decrypt(_jwe_key)
        payload = json.loads(cipher.payload.decode("utf-8"))
        if "exp" in payload:
            if datetime.now() > datetime.fromtimestamp(payload["exp"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
            del payload["exp"]
        return payload
    except (jwe.JWException, ValueError, binascii.Error):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def verification_code(
        length: int,
):
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))
