from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Enum, Boolean, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.orm import class_mapper
from sqlalchemy.event import listen
from datetime import datetime
from enum import Enum as EnumClass
from pydantic import BaseModel
from typing import Dict


@as_declarative()
class Base:
    """
    基础模型类，包含通用方法
    """

    def dict(self):
        """将 SQLAlchemy 模型对象转换为字典"""
        return {column.key: str(getattr(self, column.key)) for column in class_mapper(self.__class__).columns}

    def update(self, target):
        """根据目标对象更新自身属性"""
        for key, val in vars(target).items():
            if key and val and hasattr(self, key):
                setattr(self, key, val)


class UserRole(EnumClass):
    """
    用户角色枚举类
    """

    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class User(Base):
    """
    用户模型类
    """

    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.STUDENT, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class EntryType(EnumClass):
    """
    文件条目类型枚举类
    """

    FILE = "file"
    DIRECTORY = "directory"


class Entry(Base):
    """
    文件条目模型类
    """

    __tablename__ = "entries"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    owner_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    entry_type = Column(Enum(EntryType), nullable=False)
    entry_path = Column(String, nullable=False, index=True)
    entry_depth = Column(Integer, nullable=False)
    storage_name = Column(String, unique=True)
    is_collaborative = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    __table_args__ = (
        Index("idx_entry_path", entry_path),  # B-TREE 主索引
        Index("idx_entry_path_prefix", entry_path, postgresql_using="gin", postgresql_ops={"entry_path": "gin_trgm_ops"}),  # 适用于 LIKE 查询
    )

    @staticmethod
    def event_entry_depth(mapper, connection, target: "Entry"):
        """在插入或更新时计算 entry_depth"""
        target.entry_depth = target.entry_path.count("/")


# 监听 Entry 类的插入和更新事件
listen(Entry, "before_insert", Entry.event_entry_depth)
listen(Entry, "before_update", Entry.event_entry_depth)


class SharedEntryPermissionType(EnumClass):
    """
    共享条目额外权限类型枚举类
    """

    READ = "read"
    READ_WRITE = "read_write"
    READ_WRITE_DELETE = "read_write_delete"
    READ_WRITE_DELETE_STICKY = "read_write_delete_sticky"  # 仅目录有效


SharedEntryPermissionKey = str


class SharedEntryPermissionValue(BaseModel):
    """
    共享条目额外权限值模型类
    """
    permission_type: SharedEntryPermissionType
    inherited: bool = False


SharedEntryPermission = Dict[SharedEntryPermissionKey, SharedEntryPermissionValue]


class SharedEntry(Base):
    """
    共享条目模型类
    """

    __tablename__ = "shared_entries"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    entry_id = Column(BigInteger, ForeignKey("entries.id"), nullable=False, index=True)
    permissions = Column(JSONB)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class SharedEntryUser(Base):
    """
    共享条目用户模型类
    """

    __tablename__ = "shared_entry_users"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    shared_entry_id = Column(BigInteger, ForeignKey("shared_entries.id"), nullable=False, index=True)  # 关联共享条目
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)  # 关联用户
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
