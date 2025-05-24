from datetime import datetime
from enum import Enum as PyEnum
from typing import Dict, List

from sqlalchemy import (
    Column,
    Float,
    Integer,
    BigInteger,
    String,
    DateTime,
    Enum,
    Index,
    ForeignKey,
    Sequence,
)
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


users_uid_sequence = Sequence("seq__users__uid", start=100000000)


class User(SQLAlchemyBaseModel, Mixin):
    """
    用户模型类
    """

    __tablename__ = "users"
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    username = Column(
        String,
        nullable=False,
    )
    password = Column(
        String,
        nullable=False,
    )
    email = Column(
        String,
        nullable=False,
        unique=True,
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )
    uid = Column(
        BigInteger,
        users_uid_sequence,
        server_default=users_uid_sequence.next_value(),
        unique=True,
        nullable=False,
    )


class EntryType(EnumClass):
    """
    文件条目类型枚举类
    """

    FILE = "file"
    DIRECTORY = "directory"


# class Entry(SQLAlchemyBaseModel, Mixin):
#     """
#     文件条目模型类
#     """

#     __tablename__ = "entries"
#     id = Column(BigInteger, primary_key=True, autoincrement=True)
#     owner_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
#     entry_type = Column(Enum(EntryType), nullable=False)
#     entry_path = Column(String, nullable=False, index=True)
#     entry_depth = Column(Integer, nullable=False)
#     storage_name = Column(String, unique=True, nullable=True, default=None)
#     is_collaborative = Column(Boolean, nullable=False, default=False)
#     created_at = Column(DateTime, nullable=False, default=datetime.now)
#     updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
#     __table_args__ = (
#         Index("idx_entry_path", entry_path),  # B-TREE 主索引
#         Index(
#             "idx_entry_path_prefix",
#             entry_path,
#             postgresql_using="gin",
#             postgresql_ops={"entry_path": "gin_trgm_ops"},
#         ),  # 适用于 LIKE 查询
#     )

#     @staticmethod
#     def event_before_insert_or_update(mapper, connection, entry: "Entry"):
#         """在插入或更新时计算 entry_depth"""
#         entry.entry_depth = entry.entry_path.count("/")


# # 监听 Entry 类的插入和更新事件
# listen(Entry, "before_insert", Entry.event_before_insert_or_update)
# listen(Entry, "before_update", Entry.event_before_insert_or_update)


class CourseDirectoryPermissionType(EnumClass):
    """
    共享条目额外权限类型枚举类
    """

    READ: str = "read"  # 用户可以读这个文件夹里的所有文件，对文件来说可以读文件内容
    WRITE: str = "write"  # 用户可以修改这个文件夹里的所有文件，对文件来说可以修改文件内容
    UPLOAD: str = "upload"  # 用户可以上传文件到这个文件夹
    DELETE: str = "delete"  # 用户可以删除这个文件夹（如果文件夹内部某个文件没有delete权限，则不能删除）和文件夹里的所有文件/文件夹，对文件来说可以删除文件


SharedEntryPermissionPath = str

CourseDirectoryPermission = Dict[SharedEntryPermissionPath, List[CourseDirectoryPermissionType]]


# class SharedEntry(SQLAlchemyBaseModel, Mixin):
#     """
#     共享条目模型类
#     """

#     __tablename__ = "shared_entries"
#     id = Column(BigInteger, primary_key=True, autoincrement=True)
#     entry_id = Column(BigInteger, ForeignKey("entries.id"), nullable=False, index=True)
#     permissions = Column(JSONB)
#     created_at = Column(DateTime, nullable=False, default=datetime.now)
#     updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


# class SharedEntryUser(SQLAlchemyBaseModel, Mixin):
#     """
#     共享条目用户模型类
#     """

#     __tablename__ = "shared_entry_users"
#     id = Column(BigInteger, primary_key=True, autoincrement=True)
#     shared_entry_id = Column(BigInteger, ForeignKey("shared_entries.id"), nullable=False, index=True)  # 关联共享条目
#     user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)  # 关联用户
#     created_at = Column(DateTime, nullable=False, default=datetime.now)
#     updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class Course(SQLAlchemyBaseModel, Mixin):
    """
    课程模型类
    """

    __tablename__ = "courses"
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    teacher_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    name = Column(
        String,
        nullable=False,
    )
    description = Column(
        String,
        nullable=False,
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class CourseDirectory(SQLAlchemyBaseModel, Mixin):
    """
    课程共享条目模型类
    """

    __tablename__ = "course_directories"
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    course_id = Column(
        BigInteger,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(
        String,
        nullable=False,
    )
    permission = Column(
        JSONB,
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class CourseDirectoryEntry(SQLAlchemyBaseModel, Mixin):
    """
    课程共享条目具体类
    """

    __tablename__ = "course_directory_entries"
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    course_directory_id = Column(
        BigInteger,
        ForeignKey("course_directories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    path = Column(
        String,
        nullable=False,
        index=True,
    )
    depth = Column(
        Integer,
        nullable=False,
    )
    type = Column(
        Enum(EntryType),
        nullable=False,
    )
    storage_name = Column(
        String,
        unique=True,
        default=None,
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    __table_args__ = (
        Index("idx__course_directory_entries__path", path),  # B-TREE 主索引
        Index(
            "idx__course_directory_entires__path__prefix",
            path,
            postgresql_using="gin",
            postgresql_ops={
                "path": "gin_trgm_ops",
            },
        ),  # 适用于 LIKE 查询
    )

    @staticmethod
    def event_before_insert_or_update(mapper, connection, course_directory_entry: "CourseDirectoryEntry"):
        course_directory_entry.depth = course_directory_entry.path.count("/")


class CourseCollaborativeDirectoryEntry(SQLAlchemyBaseModel, Mixin):
    """
    课程共享可协作条目具体类
    """

    __tablename__ = "course_collaborative_directory_entries"
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    course_id = Column(
        BigInteger,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    storage_name = Column(
        String,
        nullable=False,
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )
    last_updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )
    last_updated_by = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )




listen(
    CourseDirectoryEntry,
    "before_insert",
    CourseDirectoryEntry.event_before_insert_or_update,
)
listen(
    CourseDirectoryEntry,
    "before_update",
    CourseDirectoryEntry.event_before_insert_or_update,
)


class CourseStudent(SQLAlchemyBaseModel, Mixin):
    """
    课程用户模型类
    """

    __tablename__ = "course_students"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    course_id = Column(
        BigInteger,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class CourseHomeworkAssignment(SQLAlchemyBaseModel, Mixin):
    """
    作业布置模型
    """

    __tablename__ = "course_homework_assignments"
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    course_id = Column(
        BigInteger,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(
        String,
    )
    description = Column(
        String,
    )
    deadline = Column(
        DateTime,
    )
    course_directory_entry_ids = Column(
        JSONB,
        nullable=False,
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )


class CourseHomeworkSubmission(SQLAlchemyBaseModel, Mixin):
    """
    作业提交模型
    """

    __tablename__ = "homework_submissions"
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    homework_assignments_id = Column(
        BigInteger,
        ForeignKey("course_homework_assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    title = Column(
        String,
    )
    description = Column(
        String,
    )
    course_directory_entry_ids = Column(
        JSONB,
        nullable=False,
    )
    grade = Column(
        Float,
    )
    feedback = Column(
        String,
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )
