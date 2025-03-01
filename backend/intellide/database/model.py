from datetime import datetime
from enum import Enum as PyEnum
from typing import Dict

from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Enum, Boolean, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import class_mapper


class Mixin:
    def dict(self):
        """将 SQLAlchemy 模型对象转换为字典"""
        return {column.key: str(getattr(self, column.key)) for column in class_mapper(self.__class__).columns}

    def update(self, target):
        """根据目标对象更新自身属性"""
        for key, val in vars(target).items():
            if key and val and hasattr(self, key):
                setattr(self, key, val)


class EnumClass(PyEnum):
    """
    枚举类基类
    """

    def __str__(self):
        # 重写 __str__，返回 enum 的值
        return str(self.value)


SQLAlchemyBaseModel = declarative_base()


class UserRole(EnumClass):
    """
    用户角色枚举类
    """

    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class User(SQLAlchemyBaseModel, Mixin):
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


class Entry(SQLAlchemyBaseModel, Mixin):
    """
    文件条目模型类
    """

    __tablename__ = "entries"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    owner_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    entry_type = Column(Enum(EntryType), nullable=False)
    entry_path = Column(String, nullable=False, index=True)
    entry_depth = Column(Integer, nullable=False)
    storage_name = Column(String, unique=True, nullable=True, default=None)
    is_collaborative = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    __table_args__ = (
        Index("idx_entry_path", entry_path),  # B-TREE 主索引
        Index("idx_entry_path_prefix", entry_path, postgresql_using="gin",
              postgresql_ops={"entry_path": "gin_trgm_ops"}),  # 适用于 LIKE 查询
    )

    @staticmethod
    def event_entry_depth(_, __, target: "Entry"):
        """在插入或更新时计算 entry_depth"""
        target.entry_depth = target.entry_path.count("/")


# 监听 Entry 类的插入和更新事件
listen(Entry, "before_insert", Entry.event_entry_depth)
listen(Entry, "before_update", Entry.event_entry_depth)


class SharedEntryPermissionType(EnumClass):
    """
    共享条目额外权限类型枚举类
    """
    NONE = "none"  # 已共享的某个目录里，如果有一个文件或目录唯独它不想共享可以用none
    READ = "read"  # 对纯文件来说可读内容，对目录来说可读里面的文件
    READ_WRITE = "read_write"  # 对纯文件来说可读写内容和删除自身，对目录来说可读写里面的文件（包括创建和删除文件）和删除自身
    READ_WRITE_STICKY = "read_write_sticky"  # 仅目录有效，只允许你在里面创建文件，只有你创建的文件有read_write权限


SharedEntryPermissionKey = str


class SharedEntryPermissionValue(PydanticBaseModel):
    """
    共享条目额外权限值模型类
    """
    permission_type: SharedEntryPermissionType
    # 默认继承父目录的权限
    # inherited: bool = False


SharedEntryPermission = Dict[SharedEntryPermissionKey, SharedEntryPermissionValue]


class SharedEntry(SQLAlchemyBaseModel, Mixin):
    """
    共享条目模型类
    """

    __tablename__ = "shared_entries"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    entry_id = Column(BigInteger, ForeignKey("entries.id"), nullable=False, index=True)
    permissions = Column(JSONB)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class SharedEntryUser(SQLAlchemyBaseModel, Mixin):
    """
    共享条目用户模型类
    """

    __tablename__ = "shared_entry_users"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    shared_entry_id = Column(BigInteger, ForeignKey("shared_entries.id"), nullable=False, index=True)  # 关联共享条目
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)  # 关联用户
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
