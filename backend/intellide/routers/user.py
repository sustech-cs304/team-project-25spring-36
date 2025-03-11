from typing import Dict
from typing import Optional

import email_validator
from fastapi import APIRouter, Depends
from passlib.hash import bcrypt
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from intellide.cache.cache import cache
from intellide.database.database import database
from intellide.database.model import User
from intellide.utils.auth import jwe_encode, verification_code, jwe_decode
from intellide.utils.email import email_send_register_code
from intellide.utils.response import ok, bad_request, internal_server_error

api = APIRouter(prefix="/user")


@api.get("/register/code")
async def user_register_code(
        email: str,
        db: AsyncSession = Depends(database),
):
    """
    发送邮箱验证码

    参数:
    - email: 邮箱地址

    返回:
    - 成功时返回空数据
    """
    result = await db.execute(select(User).where(User.email == email))
    user: User = result.scalar()
    if user:
        return bad_request("Email has been registered")
    try:
        email_validator.validate_email(email)
    except:
        return bad_request("Email format is incorrect")
    code = verification_code(length=6)
    await cache.set(f"register:code:{email}", code, ttl=300)
    if not await email_send_register_code(email, code):
        return bad_request("Send email failed. Please try again later.")
    return ok()


class UserRegisterRequest(BaseModel):
    username: str
    password: str
    email: str
    code: str


@api.post("/register")
async def user_register(
        request: UserRegisterRequest,
        db: AsyncSession = Depends(database),
):
    """
    创建新用户

    参数:
    - user_register: 包含用户名、密码和角色的 UserRegister 对象
    - db: 数据库会话

    返回:
    - 成功时返回包含用户的JWT
    """
    try:
        code = await cache.get(f"register:code:{request.email}")
        if not code:
            return bad_request("Register code expired or not exist")
        if code != request.code:
            return bad_request("Register code is incorrect")
        user = User(
            username=request.username,
            password=bcrypt.hash(request.password),
            email=request.email,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return ok(
            data={
                "user_id": user.id,
                "token": jwe_encode(data={"user_id": user.id}, exp_hours=24)
            }
        )
    except IntegrityError:
        await db.rollback()
        return bad_request("Email already exists")


class UserLoginRequest(BaseModel):
    email: str
    password: str


@api.post("/login")
async def user_login(
        request: UserLoginRequest,
        db: AsyncSession = Depends(database),
):
    """
    用户登录

    参数:
    - user_login: 包含用户名和密码的 UserLogin 对象
    - db: 数据库会话

    返回:
    - 成功时返回包含用户的JWT
    - 失败时返回错误信息
    """
    result = await db.execute(select(User).where(User.email == request.email))
    user: User = result.scalar()
    if not user:
        return bad_request(message="Invalid username")
    if not bcrypt.verify(request.password, user.password):
        return bad_request(message="Invalid password")
    return ok(
        data={
            "user_id": user.id,
            "token": jwe_encode(data={"user_id": user.id}, exp_hours=24)
        }
    )


class UserPutRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None


@api.get("")
async def user_get(
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    """
    获取用户信息

    参数:
    - access_info: 通过 JWT 验证后的用户信息
    - db: 数据库会话

    返回:
    - 成功时返回用户信息
    """
    result = await db.execute(select(User).where(User.id == access_info["user_id"]))
    user: User = result.scalar()
    if not user:
        return internal_server_error()
    user.password = None
    return ok(data=user.dict())


@api.put("")
async def user_put(
        request: UserPutRequest,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    """
    更新用户信息

    参数:
    - user_update: 包含要更新的用户名、密码和角色的 UserUpdate 对象
    - access_info: 通过 JWT 验证后的用户信息
    - db: 数据库会话

    返回:
    - 成功时返回包含用户的JWT
    """
    if request.password:
        request.password = bcrypt.hash(request.password)
    result = await db.execute(select(User).where(User.id == access_info["user_id"]))
    user: User = result.scalar()
    if not user:
        return bad_request(message="User not found")
    user.update(request)
    await db.commit()
    await db.refresh(user)
    return ok(
        data={
            "user_id": user.id,
            "token": jwe_encode(data={"user_id": user.id}, exp_hours=24)
        }
    )
