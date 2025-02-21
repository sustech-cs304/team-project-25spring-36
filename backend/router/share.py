from fastapi import APIRouter, Depends
from typing import Optional, List
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.util.auth import jwt_encode, jwt_verify
from backend.util.response import ok, bad_request, internal_server_error
from backend.db.engine import database
from backend.db.model import SharedEntry, Entry, User, EntryType, SharedEntryPermission

router = APIRouter(prefix="/share")


class SharedEntryPermissionCreate(BaseModel):
    shared_entry_sub_path: str
    permission: str


@router.post("/code/create")
async def entry_share_code_create(
    entry_path: str,
    permissions: Optional[List[SharedEntryPermissionCreate]] = None,
    exp_hours: Optional[int] = None,
    access_info: dict = Depends(jwt_verify),
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
    # 生成共享链接的 JWT
    share_jwt = jwt_encode(
        data={
            "entry_path": entry_path,
            "permissions": [p.model_dump() for p in permissions] if permissions else None,
            "owner_id": access_info["user_id"],
        },
        exp_hours=exp_hours,
    )
    return ok(data=share_jwt)


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
        share_info = jwt_verify(token=share_code)
        if "entry_path" not in share_info or "permissions" not in share_info or "owner_id" not in share_info:
            return bad_request(message="Invalid share code")
        # 添加共享记录
        shared_entry = SharedEntry(
            entry_id=share_info["entry_id"],
            owner_id=share_info["owner_id"],
            share_with=access_info["user_id"],
        )
        db.add(shared_entry)
        db.refresh(shared_entry)
        # 添加共享权限
        if share_info["permissions"]:
            for permission in [SharedEntryPermissionCreate.model_validate(p) for p in share_info["permissions"]]:
                db.add(
                    SharedEntryPermission(
                        shared_entry_id=shared_entry.id,
                        shared_entry_sub_path=permission.shared_entry_sub_path,
                        permission=permission.permission,
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
        for shared_entry in db.query(SharedEntry).filter(SharedEntry.share_with == access_info["user_id"]).all():
            entry: Entry = db.query(Entry).filter(Entry.id == shared_entry.entry_id).first()
            shared_entry_info = {
                "owner_id": entry.owner_id,
                "owner_name": db.query(User).filter(User.id == entry.owner_id).first().username,
                "entries": [e.to_dict() for e in [entry, *db.query(Entry).filter(Entry.entry_path.like(f"{entry.entry_path}%")).all()]],
                "permissions": [
                    p.to_dict() for p in db.query(SharedEntryPermission).filter(SharedEntryPermission.shared_entry_id == shared_entry.id).all()
                ],
            }
            shared_entries.append(shared_entry_info)
        return ok(data=shared_entries)
    except:
        return internal_server_error()
