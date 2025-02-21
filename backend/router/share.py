from fastapi import APIRouter, Depends
from typing import Optional, List
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.util.encrypt import jwt_encode, jwt_verify
from backend.util.response import ok, bad_request, internal_server_error
from backend.util.path import path_normalize, path_prefix
from backend.database.engine import database
from backend.database.model import SharedEntry, Entry, User, SharedEntryExtraPermissionType, SharedEntryExtraPermission, SharedEntryUser

router = APIRouter(prefix="/share")


class SharedEntryPermissionCreate(BaseModel):
    shared_entry_sub_path: str
    permission: SharedEntryExtraPermissionType
    inherited: bool = False


@router.post("/code/create")
async def entry_share_code_create(
    entry_path: str,
    permissions: Optional[List[SharedEntryPermissionCreate]] = None,
    exp_hours: Optional[int] = None,
    access_info: dict = Depends(jwt_verify),
    db: Session = Depends(database),
):
    """
    生成共享代码

    参数:
    - entry_path: 文件或目录路径
    - permissions: 权限列表（可选）
    - exp_hours: JWT 过期时间（小时）（可选）
    - access_info: 通过 JWT 验证后的用户信息

    返回:
    - 成功时返回共享代码
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
        # 生成共享代码
        return ok(
            jwt_encode(
                data={
                    "share_entry_id": shared_entry.id,
                },
                exp_hours=exp_hours,
            )
        )
    except:
        db.rollback()
        return internal_server_error()


@router.get("/code/parse")
async def entry_share_code_parse(
    share_code: str,
    access_info: dict = Depends(jwt_verify),
    db: Session = Depends(database),
):
    """
    解析共享代码

    参数:
    - share_code: 共享代码
    - access_info: 通过 JWT 验证后的用户信息
    - db: 数据库会话

    返回:
    - 成功时返回空数据
    """
    try:
        # 解析共享链接的 JWT
        try:
            share_info = jwt_verify(token=share_code)
        except:
            return bad_request(message="Invalid share code")
        if "share_entry_id" not in share_info:
            return bad_request(message="Invalid share code")
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
                "entries": [e.to_dict() for e in [entry, *db.query(Entry).filter(Entry.entry_path.like(f"{entry.entry_path}%")).all()]],
                "permissions": [
                    p.to_dict()
                    for p in db.query(SharedEntryExtraPermission).filter(SharedEntryExtraPermission.shared_entry_id == shared_entry.id).all()
                ],
            }
            shared_entries.append(shared_entry_info)
        return ok(data=shared_entries)
    except:
        return internal_server_error()
