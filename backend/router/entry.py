import uuid
import aiofiles
import os

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from backend.util.encrypt import jwt_verify
from backend.util.response import ok, bad_request, internal_server_error
from backend.util.path import path_normalize
from backend.database.engine import database
from backend.database.model import Entry, EntryType
from backend.config import ENTRY_STORAGE_PATH


router = APIRouter(prefix="/entry")


@router.post("")
async def entry_post(
    entry_type: EntryType,
    entry_path: str,
    file: UploadFile = File(None),
    db: Session = Depends(database),
    access_info: dict = Depends(jwt_verify),
):
    """
    上传文件或创建目录

    参数:
    - entry_type: 文件类型(FILE 或 DIRECTORY)
    - entry_path: 文件或目录路径
    - file: 上传的文件(可选)
    - db: 数据库会话
    - access_info: 访问信息(通过 JWT 验证后的用户信息)

    返回:
    - 成功时返回空响应
    """
    try:
        # 验证文件路径
        entry_path = path_normalize(entry_path)
        if not entry_path:
            return bad_request(message="Invalid entry path")
        # 获取用户 ID
        owner_id = access_info["user_id"]
        # 验证文件是否已存在
        if db.query(Entry).filter(Entry.entry_path == entry_path, Entry.owner_id == owner_id).first() is not None:
            return bad_request(message="Entry already exists")
        # 验证及自动创建父目录
        create_parent_directories(db, entry_path, owner_id)
        # 创建 Entry 记录
        if entry_type == EntryType.FILE:
            # 验证文件是否为空
            if file is None:
                return bad_request(message="Missing file")
            # 生成文件别名
            alias = uuid.uuid4().hex
            # 异步保存文件到指定目录
            async with aiofiles.open(os.path.join(ENTRY_STORAGE_PATH, alias), "wb") as buf:
                while chunk := await file.read(1024 * 1024):  # 逐块读取 1MB
                    await buf.write(chunk)
            # 创建新的 Entry 记录
            db.add(
                Entry(
                    owner_id=owner_id,
                    entry_type=entry_type,
                    entry_path=entry_path,
                    entry_depth=entry_path.count("/"),
                    alias=alias,
                )
            )
        elif entry_type == EntryType.DIRECTORY:
            # 创建新的目录 Entry 记录
            db.add(
                Entry(
                    owner_id=owner_id,
                    entry_type=entry_type,
                    entry_path=entry_path,
                    entry_depth=entry_path.count("/"),
                    alias=None,
                )
            )
        else:
            return internal_server_error()
        # 提交数据库事务
        db.commit()
        return ok()
    except:
        db.rollback()
        return internal_server_error()


@router.delete("")
async def entry_delete(
    entry_path: str,
    db: Session = Depends(database),
    access_info: dict = Depends(jwt_verify),
):
    """
    删除文件或目录

    参数:
    - entry_path: 文件或目录路径
    - db: 数据库会话
    - access_info: 访问信息（通过 JWT 验证后的用户信息）

    返回:
    - 成功时返回空响应
    """
    try:
        # 规范化文件路径
        entry_path = path_normalize(entry_path)
        if not entry_path:
            return bad_request(message="Invalid entry path")
        # 获取用户 ID
        owner_id = access_info["user_id"]
        # 查询 Entry 记录
        entry = db.query(Entry).filter(Entry.entry_path == entry_path, Entry.owner_id == owner_id).first()
        # 验证文件是否存在
        if entry is None:
            return bad_request(message="Entry not found")
        if entry.entry_type == EntryType.FILE:
            # 删除文件
            await aiofiles.os.remove(os.path.join(ENTRY_STORAGE_PATH, entry.alias))
            db.delete(entry)
        elif entry.entry_type == EntryType.DIRECTORY:
            # 删除目录及其子项
            for sub_entry in db.query(Entry).filter(Entry.entry_path.like(f"{entry_path}%"), Entry.owner_id == owner_id).all():
                if sub_entry.entry_type == EntryType.FILE:
                    await aiofiles.os.remove(os.path.join(ENTRY_STORAGE_PATH, sub_entry.alias))
                elif sub_entry.entry_type == EntryType.DIRECTORY:
                    pass
                else:
                    return internal_server_error()
                db.delete(sub_entry)
            db.delete(entry)
        else:
            return internal_server_error()
        # 提交数据库事务
        db.commit()
        return ok()
    except:
        db.rollback()
        return internal_server_error()


@router.put("")
async def entry_put(
    entry_path: str,
    new_entry_path: str,
    db: Session = Depends(database),
    access_info: dict = Depends(jwt_verify),
):
    """
    移动文件或目录

    参数:
    - entry_path: 原文件或目录路径
    - new_entry_path: 新文件或目录路径
    - db: 数据库会话
    - access_info: 访问信息（通过 JWT 验证后的用户信息）

    返回:
    - 成功时返回空响应
    """
    try:
        # 规范化文件路径
        entry_path, new_entry_path = path_normalize(entry_path), path_normalize(new_entry_path)
        if not entry_path or not new_entry_path:
            return bad_request(message="Invalid entry path")
        # 验证文件路径是否相同
        if entry_path == new_entry_path:
            return bad_request(message="Entry path unchanged")
        # 获取用户 ID
        owner_id = access_info["user_id"]
        # 查询 Entry 记录
        entry = db.query(Entry).filter(Entry.entry_path == entry_path, Entry.owner_id == owner_id).first()
        # 验证文件是否存在
        if entry is None:
            return bad_request(message="Entry not found")
        # 验证新文件是否已存在
        if db.query(Entry).filter(Entry.entry_path == new_entry_path, Entry.owner_id == owner_id).first() is not None:
            return bad_request(message="New entry already exists")
        # 验证及自动创建父目录
        create_parent_directories(db, new_entry_path, owner_id)
        # 移动文件或目录
        entry.entry_path = new_entry_path
        entry.entry_depth = entry.entry_path.count("/")
        if entry.entry_type == EntryType.DIRECTORY:
            for sub_entry in db.query(Entry).filter(Entry.entry_path.like(f"{entry_path}%"), Entry.owner_id == owner_id).all():
                sub_entry.entry_path = new_entry_path + sub_entry.entry_path[len(entry_path) :]
                sub_entry.entry_depth = sub_entry.entry_path.count("/")
        # 提交数据库事务
        db.commit()
        return ok()
    except:
        db.rollback()
        return internal_server_error()


@router.get("")
async def entry_get(
    entry_path: str,
    db: Session = Depends(database),
    access_info: dict = Depends(jwt_verify),
):
    """
    获取文件或目录信息

    参数:
    - entry_path: 文件或目录路径
    - db: 数据库会话
    - access_info: 访问信息（通过 JWT 验证后的用户信息）

    返回:
    - 成功时返回文件或目录信息
    """
    try:
        # 规范化文件路径
        entry_path = path_normalize(entry_path)
        if not entry_path:
            return bad_request(message="Invalid entry path")
        # 获取用户 ID
        owner_id = access_info["user_id"]
        # 查询 Entry 记录
        entry = db.query(Entry).filter(Entry.entry_path == entry_path, Entry.owner_id == owner_id).first()
        # 验证文件是否存在
        if entry is None:
            return bad_request(message="Entry not found")
        # 返回文件或目录信息
        return ok(
            data=[entry.to_dict() for entry in db.query(Entry).filter(Entry.entry_path.like(f"{entry_path}%"), Entry.owner_id == owner_id).all()]
        )
    except:
        return internal_server_error()


@router.get("/download")
async def entry_get_file(
    entry_path: str,
    db: Session = Depends(database),
    access_info: dict = Depends(jwt_verify),
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
        # 规范化文件路径
        entry_path = path_normalize(entry_path)
        if not entry_path:
            return bad_request(message="Invalid entry path")
        # 获取用户 ID
        owner_id = access_info["user_id"]
        # 查询 Entry 记录
        entry = db.query(Entry).filter(Entry.entry_path == entry_path, Entry.owner_id == owner_id).first()
        # 验证文件是否存在
        if entry is None:
            return bad_request(message="Entry not found")
        # 验证文件类型
        if entry.entry_type != EntryType.FILE:
            return bad_request(message="Entry is not a file")
        # 返回文件内容
        async with aiofiles.open(os.path.join(ENTRY_STORAGE_PATH, entry.alias), "rb") as buf:
            return await buf.read()
    except:
        return internal_server_error()


def create_parent_directories(db: Session, entry_path: str, owner_id: int):
    """
    验证及自动创建父目录

    参数:
    - db: 数据库会话
    - entry_path: 文件或目录路径
    - owner_id: 用户 ID
    """
    path = ""
    depth = 0
    for seg in entry_path.strip("/").split("/")[:-1]:
        path += "/" + seg
        depth += 1
        if db.query(Entry).filter(Entry.entry_path == path, Entry.owner_id == owner_id).first() is None:
            db.add(
                Entry(
                    owner_id=owner_id,
                    entry_type=EntryType.DIRECTORY,
                    entry_path=path,
                    entry_depth=depth,
                    alias=None,
                )
            )
