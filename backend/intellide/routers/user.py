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

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


from intellide.database.engine import database
from intellide.database.model import UserRole, User
from intellide.utils.cache import cache
from intellide.utils.encrypt import jwt_encode, jwt_decode
from intellide.utils.response import ok, bad_request, internal_server_error

api = APIRouter(prefix="/user")


class UserRegisterRequest(BaseModel):
    username: str
    password: str
    email: str
    code: str
    role: UserRole




# QQ邮箱配置
SMTP_SERVER = 'smtp.qq.com'
SMTP_PORT = 465
SENDER_EMAIL = 'fsht12345@qq.com'  # 替换为您的QQ邮箱
SENDER_PASSWORD = 'eflyqjkfcfdugfed'  # 替换为您的QQ邮箱授权码

async def send_verification_email(recipient_email: str, verification_code: str):
    """
    异步发送验证码邮件
    
    Args:
        recipient_email: 收件人邮箱地址
        verification_code: 验证码
    """
    try:
        # 创建邮件内容
        message = MIMEMultipart()
        message['From'] = SENDER_EMAIL
        message['To'] = recipient_email
        message['Subject'] = 'Intellide验证码'
        
        # 邮件正文
        body = f"""
        <html>
        <body>
            <h2>Intellide验证码</h2>
            <p>您的验证码是: <strong>{verification_code}</strong></p>
            <p>验证码有效期为5分钟，请勿将验证码泄露给他人。</p>
            <p>如果这不是您的操作，请忽略此邮件。</p>
        </body>
        </html>
        """
        
        # 添加HTML内容
        message.attach(MIMEText(body, 'html'))
        
        # 使用async with自动处理连接的关闭
        async with aiosmtplib.SMTP(hostname=SMTP_SERVER, port=SMTP_PORT, use_tls=True) as smtp:
            await smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            await smtp.send_message(message)
        
    except Exception as e:
        raise e

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
    code = secrets.choice(string.ascii_uppercase + string.digits)
    await cache.set(f"register:code:{email}", code, ttl=300)
    # TODO: 发送邮件
    try:
        await send_verification_email(email, code)
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
            return bad_request("Invalid code")
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


class UserUpdateRequest(BaseModel):
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
    return ok(data=user.dict())


@api.put("")
async def user_update(
        request: UserUpdateRequest,
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


