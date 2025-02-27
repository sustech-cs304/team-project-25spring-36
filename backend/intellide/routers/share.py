import os
from typing import Optional, Set, Dict, Sequence

import aiofiles
from fastapi import APIRouter, Depends, WebSocket
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from intellide.config import STORAGE_PATH
from intellide.database.engine import database
from intellide.database.model import (
    User,
    Entry,
    SharedEntry,
    SharedEntryPermission,
    SharedEntryUser,
)
from intellide.utils.encrypt import jwt_encode, jwt_verify
from intellide.utils.path import path_normalize
from intellide.utils.response import ok, bad_request, internal_server_error

api = APIRouter(prefix="/share")
ws = APIRouter(prefix="/share")


class ShareTokenCreateRequest(BaseModel):
    entry_path: str
    permissions: Optional[SharedEntryPermission] = None


@api.post("/token/create")
async def create_share_token(
        request: ShareTokenCreateRequest,
        exp_hours: Optional[int] = None,
        access_info: Dict = Depends(jwt_verify),
        db: AsyncSession = Depends(database),
):
    """
    生成共享令牌

    参数:
    - entry_path: 文件或目录路径
    - permissions: 权限列表（可选）
    - exp_hours: JWT 过期时间（小时）（可选）
    - access_info: 通过 JWT 验证后的用户信息

    返回:
    - 成功时返回共享令牌
    """
    try:
        # 验证文件路径
        try:
            request.entry_path = path_normalize(request.entry_path)
        except:
            return bad_request(message="Invalid entry path")
        # 查询文件
        result = await db.execute(
            select(Entry).where(Entry.entry_path == request.entry_path, Entry.owner_id == access_info["user_id"]))
        root_entry: Entry = result.scalar()
        if root_entry is None:
            return bad_request(message="Entry not found")

        # TODO: 验证权限类型合法性

        # 添加共享记录
        shared_entry = SharedEntry(entry_id=root_entry.id, permissions=[p.dict() for p in request.permissions])
        db.add(shared_entry)
        await db.commit()
        await db.refresh(shared_entry)
        # 生成共享令牌
        return ok(
            jwt_encode(
                data={
                    "shared_entry_id": shared_entry.id,
                },
                exp_hours=exp_hours,
            )
        )
    except:
        await db.rollback()
        return internal_server_error()


class ShareTokenParseRequest(BaseModel):
    token: str


@api.post("/token/parse")
async def share_token_parse(
        request: ShareTokenParseRequest,
        access_info: Dict = Depends(jwt_verify),
        db: AsyncSession = Depends(database),
):
    """
    解析共享令牌

    参数:
    - share_token: 共享令牌
    - access_info: 通过 JWT 验证后的用户信息
    - db: 数据库会话

    返回:
    - 成功时返回空数据
    """
    try:
        # 解析共享令牌的 JWT
        try:
            share_info = jwt_verify(token=request.token)
        except:
            return bad_request(message="Invalid share token")
        # 验证共享令牌字段
        if "shared_entry_id" not in share_info:
            return bad_request(message="Invalid share token")
        # 添加共享记录
        db.add(
            SharedEntryUser(
                shared_entry_id=share_info["shared_entry_id"],
                user_id=access_info["user_id"],
            )
        )
        await db.commit()
        return ok()
    except:
        await db.rollback()
        return internal_server_error()


@api.get("/list")
async def shared_entry_list(
        db: AsyncSession = Depends(database),
        access_info: Dict = Depends(jwt_verify),
):
    """
    获取共享记录列表

    参数:
    - db: 数据库会话
    - access_info: 通过 JWT 验证后的用户信息

    返回:
    - 成功时返回共享记录列表
    """
    try:
        shared_entries = []
        # 查询共享记录
        result = await db.execute(select(SharedEntryUser).where(SharedEntryUser.user_id == access_info["user_id"]))
        shared_entry_users: Sequence[SharedEntryUser] = result.scalars().all()
        for shared_entry_user in shared_entry_users:
            result = await db.execute(select(SharedEntry).where(SharedEntry.id == shared_entry_user.shared_entry_id))
            shared_entry: SharedEntry = result.scalar()
            result = await db.execute(select(Entry).where(Entry.id == shared_entry.entry_id))
            root_entry: Entry = result.scalar()
            result = await db.execute(select(User).where(User.id == root_entry.owner_id))
            owner: User = result.scalar()
            result = await db.execute(select(Entry).where(Entry.entry_path.like(f"{root_entry.entry_path}%")))
            entries: Sequence[Entry] = result.scalars().all()
            shared_entry_info = {
                "owner_id": root_entry.owner_id,
                "owner_name": owner.username,
                "entries": [e.dict() for e in entries],
                "permissions": shared_entry.permissions,
            }
            shared_entries.append(shared_entry_info)
        return ok(data=shared_entries)
    except:
        return internal_server_error()


class CollaborativeWebSocketManager:
    def __init__(self):
        self.conns: Dict[int, Set[WebSocket]] = {}

    async def connect(
            self,
            entry_id: int,
            websocket: WebSocket,
    ):
        """
        连接 WebSocket 并添加到连接管理器

        参数:
        - entry_id: 文件条目 ID
        - websocket: WebSocket 连接对象
        """
        await websocket.accept()
        if entry_id not in self.conns:
            self.conns[entry_id] = set()
        self.conns[entry_id].add(websocket)

    def disconnect(
            self,
            entry_id: int,
            websocket: WebSocket,
    ):
        """
        断开 WebSocket 连接并从连接管理器中移除

        参数:
        - entry_id: 文件条目 ID
        - websocket: WebSocket 连接对象
        """
        self.conns[entry_id].remove(websocket)
        if not self.conns[entry_id]:
            del self.conns[entry_id]

    async def broadcast(
            self,
            entry_id: int,
            text: str,
    ):
        """
        广播消息到所有连接的 WebSocket

        参数:
        - entry_id: 文件条目 ID
        - text: 要广播的消息
        """
        if entry_id in self.conns:
            for conn in self.conns[entry_id]:
                await conn.send_text(text)


manager = CollaborativeWebSocketManager()


@ws.websocket("/collaborative/subscribe")
async def shared_entry_collaborative_subscribe(
        websocket: WebSocket,
        entry_id: int,
        shared_entry_id: Optional[int] = None,
        db: AsyncSession = Depends(database),
        access_info=Depends(jwt_verify),
):
    """
    订阅共享条目协作

    参数:
    - websocket: WebSocket 连接对象
    - entry_id: 文件条目 ID
    - shared_entry_id: 共享条目 ID (如果是文件的所有者则可以为空)
    - db: 数据库会话
    - access_info: 通过 JWT 验证后的用户信息
    """
    # 校验
    result = await db.execute(select(Entry).where(Entry.id == entry_id))
    entry: Entry = result.scalar()
    if entry is None or not entry.is_collaborative:
        await websocket.close(code=1008)
        return

    # TODO: 验证用户是否有权限访问共享文件

    storage_path = os.path.join(STORAGE_PATH, entry.storage_name)
    # 连接 WebSocket
    await manager.connect(
        entry_id,
        websocket,
    )
    # 接收消息
    try:
        # 发送文件
        async with aiofiles.open(storage_path, "rb") as fp:
            await websocket.send_bytes(await fp.read())
        while True:
            data = await websocket.receive_text()

            # TODO: 使用 OT or CRDT进行实时协作

    except:
        manager.disconnect(
            entry_id,
            websocket,
        )
