from sqlalchemy import Column, BigInteger, String, DateTime, Enum, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime
from enum import Enum as EnumClass

from backend.db.engine import engine

Base = declarative_base()


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
    alias = Column(String)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class EntrySharePermission(Base):
    __tablename__ = "entry_share_permissions"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    entry_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    entry_permission_read = Column(Boolean, nullable=False)
    entry_permission_write = Column(Boolean, nullable=False)
    entry_permission_execute = Column(Boolean, nullable=False)
    entry_permission_stick = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


Base.metadata.create_all(engine)
