from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, Depends

from backend.database.engine import database
from backend.database.model import UserRole, User
from backend.util.encrypt import jwt_encode, jwt_verify
from backend.util.response import ok, bad_request, internal_server_error

api = APIRouter(prefix="/user")


class UserRegister(BaseModel):
    username: str
    password: str
    role: UserRole


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None


@api.post("/register")
async def user_register(
    user_register: UserRegister,
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
        user = User(username=user_register.username, password=user_register.password, role=user_register.role)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return ok(data=jwt_encode(data={"user_id": user.id, "user_role": str(user.role)}, exp_hours=24))
    except IntegrityError:
        await db.rollback()
        return bad_request("Username already exists")
    except:
        await db.rollback()
        return internal_server_error()


@api.post("/login")
async def user_login(
    user_login: UserLogin,
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
    try:
        result = await db.execute(select(User).where(User.username == user_login.username))
        user: User = result.scalar()
        if not user or user.password != user_login.password:
            return bad_request(message="Invalid username or password")
        return ok(data=jwt_encode(data={"user_id": user.id, "user_role": str(user.role)}, exp_hours=24))
    except:
        return internal_server_error()


@api.post("/update")
async def user_update(
    user_update: UserUpdate,
    access_info: dict = Depends(jwt_verify),
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
        result = await db.execute(select(User).where(User.id == access_info["user_id"]))
        user: User = result.first()
        if not user:
            return bad_request(message="User not found")
        user.update(user_update)
        await db.commit()
        await db.refresh(user)
        return ok(data=jwt_encode(data={"user_id": user.id, "user_role": str(user.role)}, exp_hours=24))
    except IntegrityError:
        await db.rollback()
        return bad_request("Username already exists")
    except:
        await db.rollback()
        return internal_server_error()
