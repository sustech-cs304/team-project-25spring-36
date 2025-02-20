import posixpath
import uuid
import aiofiles

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from pathvalidate import is_valid_filepath

from backend.util.auth import jwt_verify
from backend.util.response import ok, bad_request, not_implement
from backend.db.engine import database
from backend.db.model import Entry, EntryType, EntrySharePermission

router = APIRouter(prefix="/entry")


@router.post("/upload")
async def entry_upload(
    entry_type: EntryType,
    entry_path: str,
    auto_make_folders: bool = False,
    file: UploadFile = File(None),
    db: Session = Depends(database),
    access_info: dict = Depends(jwt_verify),
):
    """
    上传文件或创建目录

    参数:
    - entry_type: 文件类型(FILE 或 DIRECTORY)
    - entry_path: 文件或目录路径
    - auto_make_folders: 是否自动创建父目录
    - file: 上传的文件(可选)
    - db: 数据库会话
    - access_info: 访问信息(通过 JWT 验证后的用户信息)

    返回:
    - 成功时返回文件或目录信息
    """
    # 验证文件路径
    if not is_valid_filepath(entry_path, platform="linux"):
        return bad_request(message="Invalid entry path")

    # 规范化文件路径
    entry_path = posixpath.normpath(entry_path)

    # 获取用户 ID
    owner_id = access_info["user_id"]

    # 验证及自动创建父目录
    path = ""
    for seg in entry_path.split("/")[:-1]:
        path += "/" + seg
        if db.query(Entry).filter(Entry.entry_path == path, Entry.owner_id == owner_id).first() is None:
            if auto_make_folders:
                db.add(
                    Entry(
                        owner_id=owner_id,
                        entry_type=EntryType.DIRECTORY,
                        entry_path=path,
                        alias=None,
                    )
                )
            else:
                return bad_request(message="Parent directory not exists")

    if entry_type == EntryType.FILE:
        # 生成文件别名
        alias = uuid.uuid4().hex

        # 异步保存文件到指定目录
        async with aiofiles.open(f"./storage/{alias}", "wb") as buf:
            while chunk := await file.read(1024 * 1024):  # 逐块读取 1MB
                await buf.write(chunk)

        # 创建新的 Entry 记录
        db.add(
            Entry(
                owner_id=owner_id,
                entry_type=entry_type,
                entry_path=entry_path,
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
                alias=None,
            )
        )
    else:
        return not_implement(message="Invalid entry type")

    # 提交数据库事务
    db.commit()
    return ok()
