from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, Depends

from backend.db.engine import database
from backend.db.model import UserRole, User
from backend.util.auth import jwt_encode, jwt_verify
from backend.util.response import ok, bad_request, internal_error

router = APIRouter(prefix="/user")


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


@router.post("/register")
async def user_register(user_register: UserRegister, db: Session = Depends(database)):
    """
    创建新用户

    参数:
    - user_register: 包含用户名、密码和角色的 UserRegister 对象
    - db: 数据库会话

    返回:
    - 成功时返回包含用户 ID 和角色的 JWT
    """
    try:
        user = User(username=user_register.username, password=user_register.password, role=user_register.role)
        db.add(user)
        db.commit()
        db.refresh(user)
        return ok(data=jwt_encode(data={"user_id": user.id, "user_role": str(user.role)}))
    except:
        db.rollback()
        return internal_error()


@router.post("/login")
async def user_login(user_login: UserLogin, db: Session = Depends(database)):
    """
    用户登录

    参数:
    - user_login: 包含用户名和密码的 UserLogin 对象
    - db: 数据库会话

    返回:
    - 成功时返回包含用户 ID 和角色的 JWT
    - 失败时返回错误信息
    """
    try:
        user = db.query(User).filter(User.username == user_login.username).first()
        if not user or user.password != user_login.password:
            return bad_request(messsage="Invalid username or password")
        return ok(data=jwt_encode(data={"user_id": user.id, "user_role": str(user.role)}))
    except:
        return internal_error()


@router.post("/update")
async def user_update(user_update: UserUpdate, access_info: str = Depends(jwt_verify), db: Session = Depends(database)):
    """
    更新用户信息

    参数:
    - user_update: 包含要更新的用户名、密码和角色的 UserUpdate 对象
    - access_info: 通过 JWT 验证后的用户信息
    - db: 数据库会话

    返回:
    - 成功时返回操作成功的信息
    """
    try:
        user_id = access_info.get("user_id")
        user = db.query(User).filter(User.id == user_id).first()
        for key, val in vars(user_update).items():
            if val:
                setattr(user, key, val)
        db.commit()
        db.refresh(user)
        return ok()
    except:
        db.rollback()
        return internal_error()
