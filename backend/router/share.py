import aiofiles
import os

from fastapi import APIRouter, Depends, Body, WebSocket, WebSocketDisconnect
from typing import Optional, List
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.util.encrypt import jwt_encode, jwt_verify
from backend.util.response import ok, bad_request, internal_server_error, forbidden
from backend.util.path import path_normalize
from backend.database.engine import database
from backend.database.model import (
    SharedEntry,
    Entry,
    User,
    SharedEntryExtraPermissionType,
    SharedEntryExtraPermission,
    SharedEntryUser,
    SharedEntryCollaborative,
    EntryType,
)
from backend.config import ENTRY_STORAGE_PATH

router = APIRouter(prefix="/share")


class SharedEntryPermissionCreate(BaseModel):
    shared_entry_sub_path: str
    permission: SharedEntryExtraPermissionType
    inherited: bool = False


@router.post("/token/create")
async def create_share_token(
    entry_path: str,
    permissions: Optional[List[SharedEntryPermissionCreate]] = None,
    exp_hours: Optional[int] = None,
    access_info: dict = Depends(jwt_verify),
    db: Session = Depends(database),
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
        entry_path = path_normalize(entry_path)
        if not entry_path:
            return bad_request(message="Invalid entry path")
        # 查询文件
        entry = db.query(Entry).filter(Entry.entry_path == entry_path, Entry.owner_id == access_info["user_id"]).first()
        if entry is None:
            return bad_request(message="Entry not found")
        # 添加共享记录
        shared_entry = SharedEntry(
            entry_id=entry.id,
        )
        db.add(shared_entry)
        db.commit()
        db.refresh(shared_entry)
        # 添加共享权限
        if permissions:
            for permission in [SharedEntryPermissionCreate.model_validate(p) for p in permissions]:
                db.add(
                    SharedEntryExtraPermission(
                        shared_entry_id=shared_entry.id,
                        shared_entry_sub_path=permission.shared_entry_sub_path,
                        permission=permission.permission,
                        inherited=permission.inherited,
                    )
                )
        db.commit()
        # 生成共享令牌
        return ok(
            jwt_encode(
                data={
                    "share_entry_id": shared_entry.id,
                },
                exp_hours=exp_hours,
            )
        )
    except:
        import traceback

        traceback.print_exc()
        db.rollback()
        return internal_server_error()


@router.post("/token/parse")
async def parse_share_token(
    share_token: str = Body(...),
    access_info: dict = Depends(jwt_verify),
    db: Session = Depends(database),
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
            share_info = jwt_verify(token=share_token)
        except:
            return bad_request(message="Invalid share token")
        if "share_entry_id" not in share_info:
            return bad_request(message="Invalid share token")
        # 添加共享记录
        db.add(
            SharedEntryUser(
                shared_entry_id=share_info["share_entry_id"],
                user_id=access_info["user_id"],
            )
        )
        db.commit()
        return ok()
    except:
        db.rollback()
        return internal_server_error()


@router.get("/list")
async def list_shared_entries(
    db: Session = Depends(database),
    access_info: dict = Depends(jwt_verify),
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
        for shared_entry_user in db.query(SharedEntryUser).filter(SharedEntryUser.user_id == access_info["user_id"]).all():
            shared_entry: SharedEntry = db.query(SharedEntry).filter(SharedEntry.id == shared_entry_user.shared_entry_id).first()
            entry: Entry = db.query(Entry).filter(Entry.id == shared_entry.entry_id).first()
            shared_entry_info = {
                "owner_id": entry.owner_id,
                "owner_name": db.query(User).filter(User.id == entry.owner_id).first().username,
                "entries": [e.to_dict() for e in db.query(Entry).filter(Entry.entry_path.like(f"{entry.entry_path}%")).all()],
                "permissions": [
                    p.to_dict()
                    for p in db.query(SharedEntryExtraPermission).filter(SharedEntryExtraPermission.shared_entry_id == shared_entry.id).all()
                ],
                "collaboratives": [
                    c.to_dict() for c in db.query(SharedEntryCollaborative).filter(SharedEntryCollaborative.shared_entry_id == shared_entry.id).all()
                ],
            }
            shared_entries.append(shared_entry_info)
        return ok(data=shared_entries)
    except:
        return internal_server_error()


class SharedEntryCollaborativeCreate(BaseModel):
    shared_entry_id: int
    shared_entry_sub_path: str


@router.post("/collaborative/create")
async def shared_entry_collaborative_create(
    shared_entry_collaborative_create: SharedEntryCollaborativeCreate,
    access_info: dict = Depends(jwt_verify),
    db: Session = Depends(database),
):
    """
    创建共享条目协作

    参数:
    - shared_entry_id: 共享条目 ID
    - shared_entry_sub_path: 共享条目子路径
    - access_info: 通过 JWT 验证后的用户信息
    - db: 数据库会话

    返回:
    - 成功时返回空数据
    """
    try:
        # 验证共享条目子路径
        shared_entry_sub_path = path_normalize(shared_entry_collaborative_create.shared_entry_sub_path)
        if not shared_entry_sub_path:
            return bad_request(message="Invalid shared entry sub path")
        # 查询共享记录
        shared_entry = db.query(SharedEntry).filter(SharedEntry.id == shared_entry_collaborative_create.shared_entry_id).first()
        if shared_entry is None:
            return bad_request(message="Shared entry not found")
        # 查询文件
        entry = db.query(Entry).filter(Entry.id == shared_entry.entry_id).first()
        if entry is None:
            return bad_request(message="Entry not found")
        # 验证权限
        if entry.owner_id != access_info["user_id"]:
            return forbidden(message="Permission denied")
        # 查询目标文件
        collborative_entry = (
            db.query(Entry)
            .filter(
                Entry.owner_id == entry.owner_id,
                Entry.entry_path == entry.entry_path + shared_entry_sub_path,
            )
            .first()
        )
        # 验证目标文件
        if collborative_entry is None:
            return bad_request(message="Collaborative entry not found")
        if collborative_entry.entry_type != EntryType.FILE:
            return bad_request(message="Collaborative entry must be a file")
        # 验证共享条目协作是否已存在
        if (
            db.query(SharedEntryCollaborative)
            .filter(
                SharedEntryCollaborative.shared_entry_id == shared_entry.id,
                SharedEntryCollaborative.shared_entry_sub_path == shared_entry_sub_path,
            )
            .first()
            is not None
        ):
            return bad_request(message="Collaborative entry already exists")
        # 添加共享条目协作
        db.add(SharedEntryCollaborative(shared_entry_id=shared_entry.id, shared_entry_sub_path=shared_entry_sub_path))
        db.commit()
        return ok()
    except:
        db.rollback()
        return internal_server_error()


class CollaborativeWebSocketManager:
    def __init__(self):
        self.conns: dict[int, set[WebSocket]] = {}

    async def connect(
        self,
        shared_entry_collaborative_id: int,
        websocket: WebSocket,
    ):
        await websocket.accept()
        if shared_entry_collaborative_id not in self.conns:
            self.conns[shared_entry_collaborative_id] = set()
        self.conns[shared_entry_collaborative_id].add(websocket)

    def disconnect(
        self,
        shared_entry_collaborative_id: int,
        websocket: WebSocket,
    ):
        self.conns[shared_entry_collaborative_id].remove(websocket)
        if not self.conns[shared_entry_collaborative_id]:
            del self.conns[shared_entry_collaborative_id]

    async def boardcast(
        self,
        shared_entry_collaborative_id: int,
        text: str,
    ):
        if shared_entry_collaborative_id in self.conns:
            for conn in self.conns[shared_entry_collaborative_id]:
                await conn.send_text(text)


collaborative_websocket_manager = CollaborativeWebSocketManager()


@router.websocket("/collaborative/subscribe/{shared_entry_collaborative_id}")
async def shared_entry_collaborative_subscribe(
    websocket: WebSocket,
    shared_entry_collaborative_id: int,
    db=Depends(database),
):
    # 校验
    shared_entry_collaborative: SharedEntryCollaborative = (
        db.query(SharedEntryCollaborative).filter(SharedEntryCollaborative.id == shared_entry_collaborative_id).first()
    )
    if shared_entry_collaborative is None:
        await websocket.close(code=1008)
        return
    shared_entry: SharedEntry = db.query(SharedEntry).filter(SharedEntry.id == shared_entry_collaborative.shared_entry_id).first()
    if shared_entry is None:
        await websocket.close(code=1008)
        return
    # 权限解析
    # 跳过
    # 查询文件
    root_entry: Entry = db.query(Entry).filter(Entry.id == shared_entry.entry_id).first()
    if root_entry is None:
        await websocket.close(code=1008)
        return
    target_entry: Entry = (
        db.query(Entry)
        .filter(Entry.entry_path == root_entry.entry_path + shared_entry_collaborative.shared_entry_sub_path, Entry.owner_id == root_entry.owner_id)
        .first()
    )
    if target_entry is None:
        await websocket.close(code=1008)
        return
    target_path = os.path.join(ENTRY_STORAGE_PATH, target_entry.alias)
    # 连接 WebSocket
    await collaborative_websocket_manager.connect(
        websocket,
        shared_entry_collaborative_id,
    )
    # 接收消息
    try:
        # 发送文件
        with aiofiles.open(target_path, "rb") as fp:
            await websocket.send(await fp.read())
        while True:
            data = await websocket.receive_text()
            # OT or CRDT
    except:
        collaborative_websocket_manager.disconnect(
            websocket,
            shared_entry_collaborative_id,
        )
