import secrets
import string
from typing import Dict
from typing import Optional

from fastapi import APIRouter, Depends
from passlib.hash import bcrypt
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from intellide.cache.cache import cache
from intellide.database.database import database
from intellide.database.model import UserRole, User
from intellide.utils.email import email_send_register_code
from intellide.utils.encrypt import jwt_encode, jwt_decode
from intellide.utils.response import ok, bad_request, internal_server_error

api = APIRouter(prefix="/user")


class UserRegisterRequest(BaseModel):
    username: str
    password: str
    email: str
    code: str
    role: UserRole


@api.get("/register/code")
async def user_register_code(
        email: str,
):
    """
    发送邮箱验证码

    参数:
    - email: 邮箱地址

    返回:
    - 成功时返回验证码
    """
    code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    await cache.set(f"register:code:{email}", code, ttl=300)
    try:
        await email_send_register_code(email, code)
    except Exception as e:
        return bad_request(f"send email failed: {str(e)}")
    return ok()


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
            return bad_request("Register code expired or not found")
        if code != request.code:
            return bad_request("Register code is incorrect")
        user = User(
            username=request.username,
            password=bcrypt.hash(request.password),
            email=request.email,
            role=request.role,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return ok(data=jwt_encode(data={"user_id": user.id, "user_role": str(user.role)}, exp_hours=24))
    except IntegrityError:
        await db.rollback()
        return bad_request("Username or email already exists")


class UserLoginRequest(BaseModel):
    username: str
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
    result = await db.execute(select(User).where(User.username == request.username))
    user: User = result.scalar()
    if not user:
        return bad_request(message="Invalid username")
    if not bcrypt.verify(request.password, user.password):
        return bad_request(message="Invalid password")
    return ok(data=jwt_encode(data={"user_id": user.id, "user_role": str(user.role)}, exp_hours=24))


class UserPutRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None


@api.get("")
async def user_get(
        access_info: Dict = Depends(jwt_decode),
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
        access_info: Dict = Depends(jwt_decode),
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
    try:
        if request.password:
            request.password = bcrypt.hash(request.password)
        result = await db.execute(select(User).where(User.id == access_info["user_id"]))
        user: User = result.scalar()
        if not user:
            return bad_request(message="User not found")
        user.update(request)
        await db.commit()
        await db.refresh(user)
        return ok(data=jwt_encode(data={"user_id": user.id, "user_role": str(user.role)}, exp_hours=24))
    except IntegrityError:
        await db.rollback()
        return bad_request("Username already exists")
