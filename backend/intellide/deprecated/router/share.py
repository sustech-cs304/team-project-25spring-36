import os
from typing import Optional, Dict, Sequence, Tuple

import aiofiles
import aiofiles.os
from fastapi import APIRouter, Depends, WebSocket, Form, File, UploadFile, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from intellide.config import STORAGE_PATH
from intellide.database.database import database
from intellide.database.model import (
    User,
    Entry,
    SharedEntry,
    CourseDirectoryPermission,
    SharedEntryUser,
    CourseDirectoryPermissionType,
    EntryType,
)
from intellide.deprecated.router.entry import download_entry, delete_entry, post_entry, move_entry
from intellide.utils.auth import jwe_encode, jwe_decode
from intellide.utils.path import path_normalize, path_prefix
from intellide.utils.response import ok, bad_request, forbidden, APIError
from intellide.utils.websocket import WebSocketManager

api = APIRouter(prefix="/share")
ws = APIRouter(prefix="/share")


class SharedEntryTokenCreateRequest(BaseModel):
    entry_path: str
    permissions: Optional[CourseDirectoryPermission] = None


@api.post("/token/create")
async def shared_entry_token_create(
        request: SharedEntryTokenCreateRequest,
        exp_hours: Optional[int] = None,
        access_info: Dict = Depends(jwe_decode),
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
    # 验证文件路径
    request.entry_path = path_normalize(request.entry_path)

    # 查询文件
    result = await db.execute(
        select(Entry).where(
            Entry.entry_path == request.entry_path,
            Entry.owner_id == access_info["user_id"]
        )
    )
    root_entry: Entry = result.scalar()
    if root_entry is None:
        return bad_request(message="Entry not found")

    # 添加共享记录
    shared_entry = SharedEntry(
        entry_id=root_entry.id,
        permissions={
            path: CourseDirectoryPermissionType(permission).value for path, permission in request.permissions.items()
        } if request.permissions else {}
    )

    db.add(shared_entry)
    await db.commit()
    await db.refresh(shared_entry)

    # 生成共享令牌
    return ok(
        {
            "id": shared_entry.id,
            "token": jwe_encode(
                data={
                    "shared_entry_id": shared_entry.id,
                },
                exp_hours=exp_hours,
            )
        }
    )


class SharedEntryTokenParseRequest(BaseModel):
    token: str


@api.post("/token/parse")
async def shared_entry_token_parse(
        request: SharedEntryTokenParseRequest,
        access_info: Dict = Depends(jwe_decode),
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
    # 解析共享令牌的 JWT
    try:
        share_info = jwe_decode(token=request.token)
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


@api.get("/info")
async def shared_entry_info_get(
        db: AsyncSession = Depends(database),
        access_info: Dict = Depends(jwe_decode),
):
    """
    获取共享记录列表

    参数:
    - db: 数据库会话
    - access_info: 通过 JWT 验证后的用户信息

    返回:
    - 成功时返回共享记录列表
    """
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
            "shared_entry_id": shared_entry.id,  # 共享条目ID,用于共享的各种操作
            "permissions": shared_entry.permissions,
        }
        shared_entries.append(shared_entry_info)
    return ok(data=shared_entries)


@api.get("")
async def shared_entry_get(
        shared_entry_id: int,
        entry_path: str,
        entry_depth: Optional[int] = None,
        db: AsyncSession = Depends(database),
        access_info: Dict = Depends(jwe_decode),
):
    """
    获取共享条目信息

    参数:
    - shared_entry_id: 共享条目 ID
    - entry_path: 文件或目录相对于共享条目的相对路径
    - entry_depth: 文件相对共享根目录的深度（可选）
    - db: 数据库会话
    - access_info: 访问信息（通过 JWT 验证后的用户信息）

    返回:
    - 成功时返回文件或目录信息
    """
    # 查询共享条目
    user_id = access_info["user_id"]
    shared_entry, root_entry = await select_shared_entry_with_root_entry_by_id(user_id, shared_entry_id, db)
    # 获取共享根目录信息
    root_entry_path = root_entry.entry_path
    root_entry_depth = root_entry.entry_depth
    # 规范化文件路径
    entry_path = path_normalize(entry_path)
    absolute_path = shared_entry_absolute_path(root_entry, entry_path)
    # 查询 Entry 记录列表
    query = select(Entry).where(Entry.entry_path.like(f"{absolute_path}%"))
    # 对于查询结果中的每个条目，检查其是否有权限
    # 首先获取所有条目
    all_entries_result = await db.execute(query)
    all_entries: Sequence[Entry] = all_entries_result.scalars().all()
    # 创建一个新的条目列表，只包含有权限的条目
    allowed_entry_ids = []
    for entry in all_entries:
        relative_path = entry.entry_path[len(root_entry_path):]
        if not verify_permissions(
                relative_path,
                shared_entry.permissions,
                (CourseDirectoryPermissionType.READ, CourseDirectoryPermissionType.READ_WRITE)
        ):
            continue

        # 如果没有在权限列表中找到，则保留该条目
        allowed_entry_ids.append(entry.id)
    # 更新查询，只包含允许的条目
    query = query.where(Entry.id.in_(allowed_entry_ids))
    # 限制文件深度
    if entry_depth:
        query = query.where(Entry.entry_depth <= entry_depth + root_entry_depth)
    result = await db.execute(query)
    entries: Sequence[Entry] = result.scalars().all()
    # 返回文件或目录信息
    return ok(data=[
        {
            **entry.dict(),  # 展开原始字典
            "entry_path": entry.entry_path[len(root_entry_path):],  # 处理路径
            "entry_depth": entry.entry_depth - root_entry_depth  # 处理深度
        }
        for entry in entries
    ])


@api.post("")
async def shared_entry_post(
        shared_entry_id: int,
        entry_path: str = Form(...),
        entry_type: EntryType = Form(...),
        is_collaborative: bool = Form(False),
        file: Optional[UploadFile] = File(None),
        db: AsyncSession = Depends(database),
        access_info: Dict = Depends(jwe_decode),
):
    """
    在共享目录中上传文件或创建目录

    参数:
    - shared_entry_id: 共享条目ID
    - entry_path: 文件或目录相对于共享条目的相对路径
    - entry_type: 条目类型（文件或目录）
    - is_collaborative: 是否支持协作（可选）
    - file: 文件内容（可选）
    - db: 数据库会话
    - access_info: 访问信息（通过 JWT 验证后的用户信息）

    返回:
    - 成功时返回空响应
    """
    # 查询共享条目
    user_id = access_info["user_id"]
    shared_entry, root_entry = await select_shared_entry_with_root_entry_by_id(user_id, shared_entry_id, db)
    # 检查用户是否具有写入权限
    if not verify_permissions(
            entry_path,
            shared_entry.permissions,
            (CourseDirectoryPermissionType.READ_WRITE,)
    ):
        return forbidden(message="No permission to post")
    # 规范化文件路径
    absolute_path = shared_entry_absolute_path(root_entry, entry_path)
    # 获取原主人用户 ID
    owner_id = root_entry.owner_id
    # 验证及自动创建父目录
    await post_entry(
        owner_id=owner_id,
        entry_path=absolute_path,
        entry_type=entry_type,
        is_collaborative=is_collaborative,
        file=file,
        db=db,
    )
    return ok()


@api.delete("")
async def shared_entry_delete(
        shared_entry_id: int,
        entry_path: str,
        db: AsyncSession = Depends(database),
        access_info: Dict = Depends(jwe_decode),
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
    # 查询共享条目
    user_id = access_info["user_id"]
    shared_entry, root_entry = await select_shared_entry_with_root_entry_by_id(user_id, shared_entry_id, db)
    # 验证文件权限
    if not verify_permissions(
            entry_path,
            shared_entry.permissions,
            (CourseDirectoryPermissionType.READ_WRITE,),
    ):
        return forbidden(message="No permission to delete")
    # 规范化文件路径
    absolute_path = shared_entry_absolute_path(root_entry, entry_path)
    # 删除文件或目录
    await delete_entry(
        owner_id=root_entry.owner_id,
        entry_path=absolute_path,
        db=db,
    )
    return ok()


class SharedEntryMoveRequest(BaseModel):
    """
    参数:
    - src_entry_path: 源文件或目录相对共享根目录的路径
    - dst_entry_path: 目标文件或目录相对共享根目录的路径
    """
    src_entry_path: str
    dst_entry_path: str


@api.put("/move")
async def shared_entry_move(
        request: SharedEntryMoveRequest,
        shared_entry_id: int,
        db: AsyncSession = Depends(database),
        access_info: Dict = Depends(jwe_decode),
):
    """
    移动文件或目录

    参数:
    - shared_entry_id: 共享条目ID
    - request: 包含文件或目录移动信息
    - db: 数据库会话
    - access_info: 访问信息（通过 JWT 验证后的用户信息）

    返回:
    - 成功时返回空响应
    """
    # 查询共享条目
    user_id = access_info["user_id"]
    shared_entry, root_entry = await select_shared_entry_with_root_entry_by_id(user_id, shared_entry_id, db)
    # 验证文件权限
    if not verify_permissions(
            request.src_entry_path,
            shared_entry.permissions,
            (CourseDirectoryPermissionType.READ_WRITE,),
    ):
        return forbidden(message="No permission to move from source")
    if not verify_permissions(
            request.dst_entry_path,
            shared_entry.permissions,
            (CourseDirectoryPermissionType.READ_WRITE,),
    ):
        return forbidden(message="No permission to move to destination")
    # 规范化文件路径
    src_absolute_path = shared_entry_absolute_path(root_entry, request.src_entry_path)
    dst_absolute_path = shared_entry_absolute_path(root_entry, request.dst_entry_path)
    # 移动文件或目录
    await move_entry(
        owner_id=root_entry.owner_id,
        src_entry_path=src_absolute_path,
        dst_entry_path=dst_absolute_path,
        db=db,
    )
    return ok()


@api.get("/download")
async def shared_entry_download(
        shared_entry_id: int,
        entry_path: str,
        db: AsyncSession = Depends(database),
        access_info: Dict = Depends(jwe_decode),
):
    """
    下载文件

    参数:
    - shared_entry_id: 共享条目ID
    - entry_path: 文件相对共享根目录的路径
    - db: 数据库会话
    - access_info: 访问信息（通过 JWT 验证后的用户信息）

    返回:
    - 成功时返回文件内容
    """
    try:
        user_id = access_info["user_id"]
        shared_entry, root_entry = await select_shared_entry_with_root_entry_by_id(user_id, shared_entry_id, db)
        if not verify_permissions(
                entry_path,
                shared_entry.permissions,
                (CourseDirectoryPermissionType.READ, CourseDirectoryPermissionType.READ_WRITE,),
        ):
            raise HTTPException(status_code=403, detail="No permission to download")
        # 获取文件路径
        absolute_path = shared_entry_absolute_path(root_entry, entry_path)
        # 获取用户 ID
        return await download_entry(absolute_path, root_entry.owner_id, db)
    except APIError as e:
        raise HTTPException(status_code=e.code(), detail=e.message())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


manager = WebSocketManager()


@ws.websocket("/collaborative/subscribe")
async def shared_entry_collaborative_subscribe(
        websocket: WebSocket,
        entry_id: int,
        shared_entry_id: Optional[int] = None,
        db: AsyncSession = Depends(database),
        access_info=Depends(jwe_decode),
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
        shared_entry: SharedEntry = (
            await db.execute(select(SharedEntry).where(SharedEntry.id == shared_entry_id))).scalar()
        if shared_entry is None:
            await websocket.close(code=1008)
            return
        root_entry = (await db.execute(select(Entry).where(Entry.id == shared_entry.entry_id))).scalar()
        if root_entry is None:
            await websocket.close(code=1008)
            return
        if not verify_permissions(
                entry.entry_path,
                shared_entry.permissions,
                (CourseDirectoryPermissionType.READ_WRITE,),
        ):
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


def verify_permissions(
        entry_path: str,
        permissions: CourseDirectoryPermission,
        allowed_permission_types: Tuple[CourseDirectoryPermissionType, ...]
) -> bool:
    """
    检查用户是否对共享目录中的指定条目路径具有某些权限之一。
    
    参数:
        entry_path: 要检查的条目相对共享根目录的路径
        permissions: 相对路径到权限的映射字典
        allowed_permission_types: 允许的权限类型列表
        
    返回:
        如果用户具有某些权限之一则返回True，否则返回False
    """
    # 检查条目路径本身是否有显式权限
    if entry_path in permissions:
        # 将字符串权限值转换为枚举类型进行比较
        permission_enum = CourseDirectoryPermissionType(permissions[entry_path])
        if permission_enum not in allowed_permission_types:
            return False
    # 递归检查父路径
    current_path = entry_path
    while current_path != "":
        # 获取父路径
        current_path = path_prefix(current_path)
        if current_path in permissions:
            # 将字符串权限值转换为枚举类型进行比较
            permission_enum = CourseDirectoryPermissionType(permissions[current_path])
            if permission_enum not in allowed_permission_types:
                return False
            break
    return True


async def select_shared_entry_with_root_entry_by_id(
        user_id: int,
        shared_entry_id: int,
        db: AsyncSession,
) -> Tuple[SharedEntry, Entry]:
    result = await db.execute(
        select(SharedEntryUser).where(
            SharedEntryUser.user_id == user_id,
            SharedEntryUser.shared_entry_id == shared_entry_id
        )
    )
    shared_entry_user: SharedEntryUser = result.scalar()
    if shared_entry_user is None:
        raise APIError(bad_request, "You have not join this shared entry")
    # 查询共享条目
    shared_entry: SharedEntry = (
        await db.execute(select(SharedEntry).where(SharedEntry.id == shared_entry_id))).scalar()
    if shared_entry is None:
        raise APIError(bad_request, "Shared entry not found")
    result = await db.execute(select(Entry).where(Entry.id == shared_entry.entry_id))
    root_entry: Entry = result.scalar()
    if root_entry is None:
        raise APIError(bad_request, "Root entry not found")
    return shared_entry, root_entry


def shared_entry_absolute_path(
        root_entry: Entry,
        relative_entry_path: str,
) -> str:
    return path_normalize(f"{root_entry.entry_path}{relative_entry_path}")
