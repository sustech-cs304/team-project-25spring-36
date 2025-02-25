from typing import Dict
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.database.engine import database
from backend.database.model import UserRole, User
from backend.util.encrypt import jwt_encode, jwt_verify
from backend.util.response import ok, bad_request, internal_server_error

api = APIRouter(prefix="/user")


class UserRegisterRequest(BaseModel):
    username: str
    password: str
    role: UserRole


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
        user = User(username=request.username, password=request.password, role=request.role)
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
    try:
        result = await db.execute(select(User).where(User.username == request.username))
        user: User = result.scalar()
        if not user or user.password != request.password:
            return bad_request(message="Invalid username or password")
        return ok(data=jwt_encode(data={"user_id": user.id, "user_role": str(user.role)}, exp_hours=24))
    except:
        return internal_server_error()


class UserUpdateRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None


@api.put("")
async def user_update(
        request: UserUpdateRequest,
        access_info: Dict = Depends(jwt_verify),
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
    except:
        await db.rollback()
        return internal_server_error()
