from sqlalchemy import Column, BigInteger, String, DateTime, Enum, Boolean, Index
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.orm import class_mapper
from datetime import datetime
from enum import Enum as EnumClass

from backend.db.engine import engine


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
    LINK = "link"


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
    __table_args__ = (Index("idx_entry_path_gin", entry_path, postgresql_using="gin"),)


class SharedEntry(Base):
    __tablename__ = "shared_entries"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    entry_id = Column(BigInteger, nullable=False, index=True)
    share_with = Column(BigInteger, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class SharedEntryPermission(Base):
    __tablename__ = "shared_entry_permissions"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    shared_entry_id = Column(BigInteger, nullable=False, index=True)
    shared_entry_sub_path = Column(String, nullable=False, index=True)
    permission = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


Base.metadata.create_all(engine)
