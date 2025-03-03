import os
import uuid
from typing import Optional, Set, Dict, Sequence, List

import aiofiles
from fastapi import APIRouter, Depends, WebSocket, Form, File, UploadFile, HTTPException
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
    SharedEntryPermissionType,
    EntryType,
)
from intellide.utils.encrypt import jwt_encode, jwt_decode
from intellide.utils.path import path_normalize, path_prefix, path_dir_base_name
from intellide.utils.response import ok, bad_request, internal_server_error
from intellide.routers.entry import find_entry, create_parent_directories
from intellide.storage.storage import async_write_file, get_file_response

api = APIRouter(prefix="/share")
ws = APIRouter(prefix="/share")


class ShareTokenCreateRequest(BaseModel):
    entry_path: str
    permissions: Optional[SharedEntryPermission] = None


@api.post("/token/create")
async def shared_entry_token_create(
        request: ShareTokenCreateRequest,
        exp_hours: Optional[int] = None,
        access_info: Dict = Depends(jwt_decode),
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

        
        # 添加共享记录
        shared_entry = SharedEntry(
            entry_id=root_entry.id,
            permissions={path: SharedEntryPermissionType(permission).value for path, permission in request.permissions.items()} if request.permissions else {}
        )
        
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
async def shared_entry_token_parse(
        request: ShareTokenParseRequest,
        access_info: Dict = Depends(jwt_decode),
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
            share_info = jwt_decode(token=request.token)
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


@api.get("/info")
async def shared_entry_info_get(
        db: AsyncSession = Depends(database),
        access_info: Dict = Depends(jwt_decode),
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
            shared_entry_info = {
                "owner_id": root_entry.owner_id,
                "owner_name": owner.username,
                "shared_entry_id": shared_entry.id, # 共享条目ID,用于共享的各种操作
                "permissions": shared_entry.permissions,
            }
            shared_entries.append(shared_entry_info)
        return ok(data=shared_entries)
    except:
        return internal_server_error()
    


@api.get("")
async def shared_entry_get(
        shared_entry_id: int,
        entry_path: str,
        entry_depth: Optional[int] = None,
        db: AsyncSession = Depends(database),
        access_info: Dict = Depends(jwt_decode),
):
    """
    获取共享条目信息

    参数:
    - shared_entry_id: 共享条目 ID
    - entry_path: 文件或目录路径
    - entry_depth: 文件深度（可选）
    - db: 数据库会话
    - access_info: 访问信息（通过 JWT 验证后的用户信息）

    返回:
    - 成功时返回文件或目录信息
    """
    # TODO: 查询SharedEntryUser
    try:

        shared_entry: SharedEntry = (await db.execute(select(SharedEntry).where(SharedEntry.id == shared_entry_id))).scalar()
        if shared_entry is None:
            return bad_request(message="Shared entry not found")
        root_entry = (await db.execute(select(Entry).where(Entry.id == shared_entry.entry_id))).scalar()
        if root_entry is None:
            return bad_request(message="Root entry not found")
        
        root_entry_path = root_entry.entry_path
        permissions :SharedEntryPermission = shared_entry.permissions

        full_path_permissions : SharedEntryPermission = {}
        for path, permission in permissions.items():
            # 将相对路径转换为绝对路径
            absolute_path = path_normalize(f"{root_entry_path}/{path}")
            full_path_permissions[absolute_path] = permission

        print("full_path_permissions", full_path_permissions)

        print("entry_path", entry_path)
        print("root_entry_path", root_entry_path)
        # 规范化文件路径
        if not entry_path.startswith(root_entry_path):
            return bad_request(message="Entry path not in shared entry")
        try:
            entry_path = path_normalize(entry_path)
        except:
            return bad_request(message="Invalid entry path")
        # 查询 Entry 记录列表
        query = select(Entry).where(Entry.entry_path.like(f"{entry_path}%"))
        
        # 对于查询结果中的每个条目，检查其是否有权限
        # 首先获取所有条目
        all_entries_result = await db.execute(query)
        all_entries: Sequence[Entry] = all_entries_result.scalars().all()
        
        # 创建一个新的条目列表，只包含有权限的条目
        allowed_entry_ids = []
        for entry in all_entries:
            path = entry.entry_path
            if not check_permission(path, root_entry_path, full_path_permissions, [SharedEntryPermissionType.READ, SharedEntryPermissionType.READ_WRITE]):
                print("entry_path", path, "not allowed")
                continue
                
            # 如果没有在权限列表中找到，则保留该条目
            allowed_entry_ids.append(entry.id)

        
        # 更新查询，只包含允许的条目

        query = query.where(Entry.id.in_(allowed_entry_ids))
        
        # 限制文件深度
        if entry_depth:
            query = query.where(Entry.entry_depth <= entry_depth)
        result = await db.execute(query)
        entries: Sequence[Entry] = result.scalars().all()
        # 返回文件或目录信息
        return ok(data=[entry.dict() for entry in entries])
    except:
        return internal_server_error()


@api.post("")
async def shared_entry_post(
        shared_entry_id: int,
        entry_path: str = Form(...),
        entry_type: EntryType = Form(...),
        is_collaborative: bool = Form(False),
        file: Optional[UploadFile] = File(None),
        db: AsyncSession = Depends(database),
        access_info: Dict = Depends(jwt_decode),
):
    """
    在共享目录中上传文件或创建目录

    参数:
    - shared_entry_id: 共享条目ID
    - entry_path: 文件或目录路径
    - entry_type: 条目类型（文件或目录）
    - is_collaborative: 是否支持协作（可选）
    - file: 文件内容（可选）
    - db: 数据库会话
    - access_info: 访问信息（通过 JWT 验证后的用户信息）

    返回:
    - 成功时返回空响应
    """
    # TODO: 查询SharedEntryUser
    try:
        # 查询共享条目
        shared_entry: SharedEntry = (await db.execute(select(SharedEntry).where(SharedEntry.id == shared_entry_id))).scalar()
        if shared_entry is None:
            return bad_request(message="Shared entry not found")
            
        # 获取根目录条目
        root_entry = (await db.execute(select(Entry).where(Entry.id == shared_entry.entry_id))).scalar()
        if root_entry is None:
            return bad_request(message="Root entry not found")
        root_entry_path = root_entry.entry_path

        # 获取权限设置
        permissions: SharedEntryPermission = shared_entry.permissions
        full_path_permissions : SharedEntryPermission = {}
        for path, permission in permissions.items():
            # 将相对路径转换为绝对路径
            absolute_path = path_normalize(f"{root_entry_path}/{path}")
            full_path_permissions[absolute_path] = permission


        # 检查用户是否具有写入权限
        if not check_permission(entry_path, root_entry_path, full_path_permissions, [SharedEntryPermissionType.READ_WRITE]):
            return bad_request(message="No permission to post")


        # 获取原主人用户 ID
        owner_id = root_entry.owner_id
        
        try:
            entry: Optional[Entry] = await find_entry(entry_path, owner_id, db, nullable=True)
            if entry is not None:
                return bad_request(message="Entry already exists")
        except ValueError as e:
            return bad_request(message=str(e))
        # 验证及自动创建父目录
        await create_parent_directories(entry_path, owner_id, db)
        # 创建 Entry 记录
        if entry_type == EntryType.FILE:
            # 验证文件是否为空
            if file is None:
                return bad_request(message="Missing file")
            # 生成文件别名
            storage_name = uuid.uuid4().hex
            # 异步保存文件到指定目录
            await async_write_file(storage_name, await file.read())
            # 创建新的 Entry 记录
            db.add(
                Entry(
                    owner_id=owner_id,
                    entry_type=entry_type,
                    entry_path=entry_path,
                    storage_name=storage_name,
                    is_collaborative=is_collaborative,
                )
            )
        elif entry_type == EntryType.DIRECTORY:
            # 创建新的目录 Entry 记录
            db.add(
                Entry(
                    owner_id=owner_id,
                    entry_type=entry_type,
                    entry_path=entry_path,
                )
            )
        else:
            return internal_server_error()
        # 提交数据库事务
        await db.commit()
        return ok()
    except:
        await db.rollback()
        return internal_server_error()




@api.delete("")
async def shared_entry_delete(
        shared_entry_id: int,
        entry_path: str,
        db: AsyncSession = Depends(database),
        access_info: Dict = Depends(jwt_decode),
):
    """
    删除共享条目中的文件或目录

    参数:
    - shared_entry_id: 共享条目ID
    - entry_path: 文件或目录路径
    - db: 数据库会话
    - access_info: 访问信息（通过 JWT 验证后的用户信息）

    返回:
    - 成功时返回空响应
    """
    try:
        # 查询共享条目
        shared_entry: SharedEntry = (await db.execute(select(SharedEntry).where(SharedEntry.id == shared_entry_id))).scalar()
        if shared_entry is None:
            return bad_request(message="Shared entry not found")
        # 获取根目录条目
        root_entry = (await db.execute(select(Entry).where(Entry.id == shared_entry.entry_id))).scalar()
        if root_entry is None:
            return bad_request(message="Root entry not found")
        root_entry_path = root_entry.entry_path
        # 获取权限设置  
        permissions: SharedEntryPermission = shared_entry.permissions
        full_path_permissions : SharedEntryPermission = {}
        for path, permission in permissions.items():
            # 将相对路径转换为绝对路径
            absolute_path = path_normalize(f"{root_entry_path}/{path}")
            full_path_permissions[absolute_path] = permission
        
        if not check_permission(entry_path, root_entry_path, full_path_permissions, [SharedEntryPermissionType.READ_WRITE]):
            return bad_request(message="No permission to delete")
        
        
        # 获取原主人用户 ID
        owner_id = root_entry.owner_id
        
        # 寻找文件或目录
        try:
            entry: Entry = await find_entry(entry_path, owner_id, db)
        except ValueError as e:
            return bad_request(message=str(e))
        if entry.entry_type == EntryType.FILE:
            # 删除文件
            await aiofiles.os.remove(os.path.join(STORAGE_PATH, entry.storage_name))
            await db.delete(entry)
        elif entry.entry_type == EntryType.DIRECTORY:
            # 删除目录及其子项
            result = await db.execute(
                select(Entry).where(Entry.entry_path.like(f"{entry_path}%"), Entry.owner_id == owner_id))
            sub_entries: Sequence[Entry] = result.scalars().all()
            for sub_entry in sub_entries:
                if sub_entry.entry_type == EntryType.FILE:
                    await aiofiles.os.remove(os.path.join(STORAGE_PATH, sub_entry.storage_name))
                await db.delete(sub_entry)
        else:
            return internal_server_error()
        # 提交数据库事务
        await db.commit()
        return ok()
    except:
        await db.rollback()
        return internal_server_error()





class EntryMoveRequest(BaseModel):
    src_entry_path: str
    dst_entry_path: str


@api.put("/move")
async def shared_entry_move(
        request: EntryMoveRequest,
        shared_entry_id: int,
        db: AsyncSession = Depends(database),
        access_info: Dict = Depends(jwt_decode),
):
    """
    移动文件或目录

    参数:
    - request: 包含文件或目录移动信息
    - db: 数据库会话
    - access_info: 访问信息（通过 JWT 验证后的用户信息）

    返回:
    - 成功时返回空响应
    """
    try:
        # 验证文件路径是否相同
        if request.src_entry_path == request.dst_entry_path:
            return bad_request(message="Entry path unchanged")
        
        # 查询共享条目
        shared_entry: SharedEntry = (await db.execute(select(SharedEntry).where(SharedEntry.id == shared_entry_id))).scalar()
        if shared_entry is None:
            return bad_request(message="Shared entry not found")
        # 获取根目录条目
        root_entry = (await db.execute(select(Entry).where(Entry.id == shared_entry.entry_id))).scalar()
        if root_entry is None:
            return bad_request(message="Root entry not found")  
        root_entry_path = root_entry.entry_path
        # 获取权限设置
        permissions: SharedEntryPermission = shared_entry.permissions
        full_path_permissions : SharedEntryPermission = {}
        for path, permission in permissions.items():
            # 将相对路径转换为绝对路径
            absolute_path = path_normalize(f"{root_entry_path}/{path}")
            full_path_permissions[absolute_path] = permission
        
        if not check_permission(request.src_entry_path, root_entry_path, full_path_permissions, [SharedEntryPermissionType.READ_WRITE]):
            return bad_request(message="No permission to move from source")
        if not check_permission(request.dst_entry_path, root_entry_path, full_path_permissions, [SharedEntryPermissionType.READ_WRITE]):
            return bad_request(message="No permission to move to destination")


        # 获取用户 ID
        owner_id = root_entry.owner_id
        try:
            src_entry: Entry = await find_entry(request.src_entry_path, owner_id, db)
            dst_entry: Entry = await find_entry(request.dst_entry_path, owner_id, db, nullable=True)
            # 断言新路径不存在
            if dst_entry is not None:
                return bad_request(message="New entry already exists")
        except ValueError as e:
            return bad_request(message=str(e))
        # 验证及自动创建父目录
        await create_parent_directories(request.dst_entry_path, owner_id, db)
        # 移动文件或目录
        if src_entry.entry_type == EntryType.DIRECTORY:
            result = await db.execute(
                select(Entry).where(Entry.entry_path.like(f"{request.src_entry_path}%"), Entry.owner_id == owner_id))
            sub_entries: Sequence[Entry] = result.scalars().all()
            for sub_entry in sub_entries:
                sub_entry.entry_path = request.dst_entry_path + sub_entry.entry_path[len(request.src_entry_path):]
        elif src_entry.entry_type == EntryType.FILE:
            src_entry.entry_path = request.dst_entry_path
        else:
            return internal_server_error()
        # 提交数据库事务
        await db.commit()
        return ok()
    except:
        await db.rollback()
        return internal_server_error()






@api.get("/download")
async def shared_entry_download(
        shared_entry_id: int,
        entry_path: str,
        db: AsyncSession = Depends(database),
        access_info: Dict = Depends(jwt_decode),
):
    """
    下载文件

    参数:
    - entry_path: 文件路径
    - db: 数据库会话
    - access_info: 访问信息（通过 JWT 验证后的用户信息）

    返回:
    - 成功时返回文件内容
    """
    try:
        # 查询共享条目
        shared_entry: SharedEntry = (await db.execute(select(SharedEntry).where(SharedEntry.id == shared_entry_id))).scalar()
        if shared_entry is None:
            return bad_request(message="Shared entry not found")
        # 获取根目录条目
        root_entry = (await db.execute(select(Entry).where(Entry.id == shared_entry.entry_id))).scalar()
        if root_entry is None:
            return bad_request(message="Root entry not found")
        root_entry_path = root_entry.entry_path
        if not check_permission(entry_path, root_entry_path, shared_entry.permissions, [SharedEntryPermissionType.READ, SharedEntryPermissionType.READ_WRITE]):
            return bad_request(message="No permission to download")
        # 获取用户 ID
        owner_id = root_entry.owner_id
        try:
            entry: Entry = await find_entry(entry_path, owner_id, db)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        # 验证文件类型
        if entry.entry_type != EntryType.FILE:
            raise HTTPException(status_code=400, detail="Entry is not a file")
        # 获取文件名
        _, file_name = path_dir_base_name(entry_path)
        # 返回文件内容
        return get_file_response(entry.storage_name, file_name)
    except HTTPException:
        raise
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
        access_info=Depends(jwt_decode),
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
    if shared_entry_id is not None:
        shared_entry: SharedEntry = (await db.execute(select(SharedEntry).where(SharedEntry.id == shared_entry_id))).scalar()
        if shared_entry is None:
            await websocket.close(code=1008)
            return
        root_entry = (await db.execute(select(Entry).where(Entry.id == shared_entry.entry_id))).scalar()
        if root_entry is None:
            await websocket.close(code=1008)
            return
        root_entry_path = root_entry.entry_path
        if not check_permission(entry.entry_path, root_entry_path, shared_entry.permissions, [SharedEntryPermissionType.READ_WRITE]):
            await websocket.close(code=1008)
            return
        
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






def check_permission(entry_path: str, root_entry_path: str, full_path_permissions: SharedEntryPermission, allowed_permission_types: List[SharedEntryPermissionType]) -> bool:
    """
    检查用户是否对共享目录中的指定条目路径具有某些权限之一。
    
    参数:
        entry_path: 要检查的条目路径
        root_entry_path: 共享目录的根路径
        full_path_permissions: 绝对路径到权限的映射字典
        allowed_permission_types: 允许的权限类型列表
        
    返回:
        如果用户具有某些权限之一则返回True，否则返回False
    """
    # 检查的条目路径是否在共享目录内部
    if not entry_path.startswith(root_entry_path):
        return False
    # 检查条目路径本身是否有显式权限
    if entry_path in full_path_permissions:
        # 将字符串权限值转换为枚举类型进行比较
        permission_enum = SharedEntryPermissionType(full_path_permissions[entry_path])
        if permission_enum not in allowed_permission_types:
            return False
    
    # 递归检查父路径
    current_path = entry_path
    while current_path != root_entry_path:
        # 获取父路径
        current_path = path_prefix(current_path)
        if current_path in full_path_permissions:
            # 将字符串权限值转换为枚举类型进行比较
            permission_enum = SharedEntryPermissionType(full_path_permissions[current_path])
            if permission_enum not in allowed_permission_types:
                return False
            break
    
    return True
