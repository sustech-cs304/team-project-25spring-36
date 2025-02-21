from sqlalchemy import Column, BigInteger, String, DateTime, Enum, Boolean, Index
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.orm import class_mapper
from datetime import datetime
from enum import Enum as EnumClass

from backend.database.engine import engine


@as_declarative()
class Base:

    def to_dict(self):
        """将 SQLAlchemy 模型对象转换为字典"""
        return {column.key: str(getattr(self, column.key)) for column in class_mapper(self.__class__).columns}


class UserRole(EnumClass):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.STUDENT, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class EntryType(EnumClass):
    FILE = "file"
    DIRECTORY = "directory"


class Entry(Base):
    __tablename__ = "entries"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    owner_id = Column(BigInteger, nullable=False, index=True)
    entry_type = Column(Enum(EntryType), nullable=False)
    entry_path = Column(String, nullable=False, index=True)
    entry_depth = Column(BigInteger, nullable=False)
    alias = Column(String, unique=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    __table_args__ = (
        Index("idx_entry_path", entry_path),  # B-TREE 主索引
        Index("idx_entry_path_prefix", entry_path, postgresql_using="gin"),  # 适用于 LIKE 查询
    )


class SharedEntry(Base):
    __tablename__ = "shared_entries"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    entry_id = Column(BigInteger, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class SharedEntryExtraPermissionType(EnumClass):
    READ = "read"
    READ_WRITE = "read_write"
    READ_WRITE_DELETE = "read_write_delete"
    READ_WRITE_DELETE_STICKY = "read_write_delete_sticky"  # 仅目录有效


class SharedEntryExtraPermission(Base):
    __tablename__ = "shared_entry_extra_permissions"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    shared_entry_id = Column(BigInteger, nullable=False, index=True)  # 关联 shared_entries
    shared_entry_sub_path = Column(String, nullable=False, index=True)  # 子文件或子目录
    permission = Column(Enum(SharedEntryExtraPermissionType), nullable=False)  # 统一存储文件和目录权限
    inherited = Column(Boolean, nullable=False, default=False)  # 是否继承（仅目录有效）
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class SharedEntryUser(Base):
    __tablename__ = "shared_entry_users"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    shared_entry_id = Column(BigInteger, nullable=False, index=True)  # 关联共享条目
    user_id = Column(BigInteger, nullable=False, index=True)  # 关联用户
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


Base.metadata.create_all(engine)
