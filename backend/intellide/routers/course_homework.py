from typing import Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from intellide.database import database
from intellide.database.model import (
    Course,
    CourseDirectory,
    CourseDirectoryEntry,
    CourseStudent,
    CourseHomeworkAssignment,
    CourseHomeworkSubmission,
)
from intellide.utils.auth import jwe_decode
from intellide.utils.response import ok, forbidden, bad_request

# 创建作业路由前缀
api = APIRouter(prefix="/course/homework")


class CourseHomeworkAssignmentCreate(BaseModel):
    """
    作业布置创建请求模型
    """

    course_id: int
    title: Optional[str]
    description: Optional[str]
    deadline: Optional[datetime]
    course_directory_entry_ids: List[int]  # CourseDirectoryEntry ID列表，指向作业问题文件


class CourseHomeworkAssignmentUpdate(BaseModel):
    """
    作业布置更新请求模型
    """

    assignment_id: int
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    course_directory_entry_ids: Optional[List[int]] = None  # CourseDirectoryEntry ID列表，指向作业问题文件


@api.post("/assignment", response_model=dict)
async def course_homework_assignment_create(
    body: CourseHomeworkAssignmentCreate,
    access_info: Dict = Depends(jwe_decode),
    db: AsyncSession = Depends(database),
):
    """
    创建作业布置（仅教师）

    参数：
        assignment: 作业布置创建请求
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        创建的作业布置对象
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 查询课程信息
    result = await db.execute(select(Course).where(Course.id == body.course_id))
    course = result.scalar()

    # 检查课程是否存在
    if not course:
        return bad_request("Course not found")

    # 检查用户是否为该课程的教师
    if course.teacher_id != user_id:
        return forbidden("Permission denied")

    # 验证文件条目是否存在且属于该课程
    for entry_id in body.course_directory_entry_ids:
        result = await db.execute(
            select(CourseDirectoryEntry, CourseDirectory)
            .join(
                CourseDirectory,
                CourseDirectoryEntry.course_directory_id == CourseDirectory.id,
            )
            .where(
                CourseDirectoryEntry.id == entry_id,
                CourseDirectory.course_id == body.course_id,
            )
        )
        entry_info = result.first()
        if not entry_info:
            return bad_request(f"Entry {entry_id} not found or not belong to this course")

    # 创建作业布置
    new_assignment = CourseHomeworkAssignment(
        course_id=body.course_id,
        title=body.title,
        description=body.description,
        deadline=body.deadline,
        course_directory_entry_ids=body.course_directory_entry_ids,
    )

    # 保存到数据库
    db.add(new_assignment)
    await db.commit()
    await db.refresh(new_assignment)

    return ok(data=new_assignment.dict())


@api.get("/assignment", response_model=List[dict])
async def course_homework_assignment_get(
    course_id: int,
    access_info: Dict = Depends(jwe_decode),
    db: AsyncSession = Depends(database),
):
    """
    获取课程的所有作业布置

    参数：
        course_id: 课程ID
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        作业布置对象列表
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 查询课程信息
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar()

    # 检查课程是否存在
    if not course:
        return bad_request("Course not found")

    # 检查用户是否有权限查看（教师或学生）
    if course.teacher_id != user_id:
        # 检查是否是课程学生
        result = await db.execute(
            select(CourseStudent).where(
                CourseStudent.course_id == course_id,
                CourseStudent.student_id == user_id,
            )
        )
        student = result.scalar()
        if not student:
            return forbidden("Permission denied")

    # 查询该课程的所有作业
    result = await db.execute(select(CourseHomeworkAssignment).where(CourseHomeworkAssignment.course_id == course_id))
    assignments = result.scalars().all()

    return ok(data=[assignment.dict() for assignment in assignments])


class CourseHomeworkSubmissionCreate(BaseModel):
    """
    作业提交创建请求模型
    """

    assignment_id: int
    title: Optional[str]
    description: Optional[str]
    course_directory_entry_ids: List[int]  # CourseDirectoryEntry ID列表，指向作业回答文件


@api.post("/submission", response_model=dict)
async def course_homework_submission_create(
    body: CourseHomeworkSubmissionCreate,
    access_info: Dict = Depends(jwe_decode),
    db: AsyncSession = Depends(database),
):
    """
    创建作业提交（仅学生）

    参数：
        submission: 作业提交创建请求
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        创建的作业提交对象
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 查询作业信息
    result = await db.execute(select(CourseHomeworkAssignment).where(CourseHomeworkAssignment.id == body.assignment_id))
    assignment = result.scalar()

    # 检查作业是否存在
    if not assignment:
        return bad_request("Assignment not found")

    # 查询课程信息
    result = await db.execute(select(Course).where(Course.id == assignment.course_id))
    course = result.scalar()

    # 检查课程是否存在
    if not course:
        return bad_request("Course not found")

    # 检查用户是否为该课程的学生
    result = await db.execute(
        select(CourseStudent).where(
            CourseStudent.course_id == assignment.course_id,
            CourseStudent.student_id == user_id,
        )
    )
    student = result.scalar()
    if not student:
        return forbidden("Only enrolled students can submit homework")

    # 检查提交截止日期
    if assignment.deadline and datetime.now() > assignment.deadline:
        return bad_request("Submission deadline has passed")

    # 验证文件条目是否存在且属于该课程并且是学生自己的
    for entry_id in body.course_directory_entry_ids:
        result = await db.execute(
            select(CourseDirectoryEntry, CourseDirectory)
            .join(
                CourseDirectory,
                CourseDirectoryEntry.course_directory_id == CourseDirectory.id,
            )
            .where(
                CourseDirectoryEntry.id == entry_id,
                CourseDirectory.course_id == assignment.course_id,
                CourseDirectoryEntry.author_id == user_id,  # 确保文件是学生自己的
            )
        )
        entry_info = result.first()
        if not entry_info:
            return bad_request(f"Entry {entry_id} not found, not part of this course, or not owned by you")

    # 创建新提交
    new_submission = CourseHomeworkSubmission(
        homework_assignments_id=body.assignment_id,  # 使用assignment_id作为homework_assignments_id
        student_id=user_id,
        title=body.title,
        description=body.description,
        course_directory_entry_ids=body.course_directory_entry_ids,
    )

    # 保存到数据库
    db.add(new_submission)
    await db.commit()
    await db.refresh(new_submission)

    # 使用模型的dict方法转换为字典
    return ok(data=new_submission.dict())


@api.get("/submission", response_model=List[dict])
async def course_homework_submission_get(
    submission_id: Optional[int] = None,
    assignment_id: Optional[int] = None,
    student_id: Optional[int] = None,
    access_info: Dict = Depends(jwe_decode),
    db: AsyncSession = Depends(database),
):
    """
    查询作业提交，支持两种查询方式：
    1. 通过submission_id查询特定提交
    2. 通过assignment_id查询某作业的所有提交（教师可附加student_id筛选特定学生）

    参数：
        submission_id: 可选，提交ID - 如果提供，直接查询该提交
        assignment_id: 可选，作业ID - 如果提供，查询该作业的所有提交
        student_id: 可选，学生ID - 教师查看特定学生提交时与assignment_id一起使用
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        作业提交对象列表
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 检查参数有效性
    if submission_id is None and assignment_id is None:
        return bad_request("Invalid parameters: need either submission_id or assignment_id")

    # 情况1: 根据submission_id查询
    if submission_id is not None:
        result = await db.execute(select(CourseHomeworkSubmission).where(CourseHomeworkSubmission.id == submission_id))
        submission = result.scalar()
        if not submission:
            return bad_request("Submission not found")

        # 查询对应的作业和课程信息
        result = await db.execute(select(CourseHomeworkAssignment).where(CourseHomeworkAssignment.id == submission.homework_assignments_id))
        assignment = result.scalar()

        result = await db.execute(select(Course).where(Course.id == assignment.course_id))
        course = result.scalar()

        # 检查权限：教师可以查看所有提交，学生只能查看自己的提交
        if course.teacher_id != user_id and submission.student_id != user_id:
            return forbidden("Permission denied")

        return ok(data=[submission.dict()])

    # 情况2: 根据assignment_id查询
    if assignment_id is not None:
        # 查询作业信息
        result = await db.execute(select(CourseHomeworkAssignment).where(CourseHomeworkAssignment.id == assignment_id))
        assignment = result.scalar()

        # 检查作业是否存在
        if not assignment:
            return bad_request("Assignment not found")

        # 查询课程信息
        result = await db.execute(select(Course).where(Course.id == assignment.course_id))
        course = result.scalar()

        # 检查课程是否存在
        if not course:
            return bad_request("Course not found")

        # 如果是教师
        if course.teacher_id == user_id:
            # 如果提供了student_id，只查询该学生的提交
            if student_id is not None:
                # 验证学生是否存在且已注册课程
                result = await db.execute(
                    select(CourseStudent).where(
                        CourseStudent.course_id == assignment.course_id,
                        CourseStudent.student_id == student_id,
                    )
                )
                student = result.scalar()
                if not student:
                    return bad_request("Student not found or not enrolled in this course")

                # 查询指定学生的所有提交
                result = await db.execute(
                    select(CourseHomeworkSubmission).where(
                        CourseHomeworkSubmission.homework_assignments_id == assignment_id,
                        CourseHomeworkSubmission.student_id == student_id,
                    )
                )
            else:
                # 查询所有学生的提交
                result = await db.execute(select(CourseHomeworkSubmission).where(CourseHomeworkSubmission.homework_assignments_id == assignment_id))
        # 如果是学生
        else:
            # 检查是否在课程中注册
            result = await db.execute(
                select(CourseStudent).where(
                    CourseStudent.course_id == assignment.course_id,
                    CourseStudent.student_id == user_id,
                )
            )
            student = result.scalar()
            if not student:
                return forbidden("Permission denied")

            # 学生只能查看自己的提交
            result = await db.execute(
                select(CourseHomeworkSubmission).where(
                    CourseHomeworkSubmission.homework_assignments_id == assignment_id,
                    CourseHomeworkSubmission.student_id == user_id,
                )
            )

        submissions = result.scalars().all()
        return ok(data=[submission.dict() for submission in submissions])


class CourseHomeworkSubmissionGrade(BaseModel):
    """
    作业提交创建请求模型
    """

    submission_id: int
    grade: float
    feedback: Optional[str]


@api.put("/submission/grade")
async def course_homework_submission_grade(
    body: CourseHomeworkSubmissionGrade,
    access_info: Dict = Depends(jwe_decode),
    db: AsyncSession = Depends(database),
):
    """
    为作业提交评分（仅教师）

    参数：
        grade_request: 评分请求，包含提交ID、分数和可选的反馈
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        更新后的作业提交对象
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 查询提交信息
    result = await db.execute(select(CourseHomeworkSubmission).where(CourseHomeworkSubmission.id == body.submission_id))
    submission = result.scalar()

    # 检查提交是否存在
    if not submission:
        return bad_request("Submission not found")

    # 查询作业信息
    result = await db.execute(select(CourseHomeworkAssignment).where(CourseHomeworkAssignment.id == submission.homework_assignments_id))
    assignment = result.scalar()

    # 查询课程信息
    result = await db.execute(select(Course).where(Course.id == assignment.course_id))
    course = result.scalar()

    # 检查用户是否为该课程的教师
    if course.teacher_id != user_id:
        return forbidden("Only course teacher can grade submissions")

    # 更新分数和反馈
    submission.grade = body.grade
    submission.feedback = body.feedback
    submission.updated_at = datetime.now()

    await db.commit()
    await db.refresh(submission)

    # 使用模型的dict方法
    return ok(data=submission.dict())


@api.delete("/assignment")
async def course_homework_assignment_delete(
    assignment_id: int,
    access_info: Dict = Depends(jwe_decode),
    db: AsyncSession = Depends(database),
):
    """
    删除作业布置（仅教师）

    参数：
        assignment_id: 要删除的作业ID
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        删除成功返回OK

    异常：
        APIError: 当用户没有权限或作业不存在时抛出
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 查询作业信息
    result = await db.execute(select(CourseHomeworkAssignment).where(CourseHomeworkAssignment.id == assignment_id))
    assignment = result.scalar()

    # 检查作业是否存在
    if not assignment:
        return bad_request("Assignment not found")

    # 查询课程信息
    result = await db.execute(select(Course).where(Course.id == assignment.course_id))
    course = result.scalar()

    # 检查用户是否为该课程的教师
    if course.teacher_id != user_id:
        return forbidden("Only course teacher can delete assignments")

    # 删除作业记录，相关联的submission会自动删除（CASCADE）
    await db.delete(assignment)
    await db.commit()

    return ok(data={"message": "Assignment deleted successfully"})


@api.delete("/submission")
async def course_homework_submission_delete(
    submission_id: int,
    access_info: Dict = Depends(jwe_decode),
    db: AsyncSession = Depends(database),
):
    """
    删除作业提交（仅教师）

    参数：
        submission_id: 要删除的提交ID
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        删除成功返回OK

    异常：
        APIError: 当用户没有权限或提交不存在时抛出
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 查询提交信息
    result = await db.execute(select(CourseHomeworkSubmission).where(CourseHomeworkSubmission.id == submission_id))
    submission = result.scalar()

    # 检查提交是否存在
    if not submission:
        return bad_request("Submission not found")

    # 查询作业信息
    result = await db.execute(select(CourseHomeworkAssignment).where(CourseHomeworkAssignment.id == submission.homework_assignments_id))
    assignment = result.scalar()

    # 查询课程信息
    result = await db.execute(select(Course).where(Course.id == assignment.course_id))
    course = result.scalar()

    # 检查用户是否为该课程的教师
    if course.teacher_id != user_id:
        return forbidden("Only course teacher can delete submissions")

    # 删除提交记录
    await db.delete(submission)
    await db.commit()

    return ok(data={"message": "Submission deleted successfully"})


@api.get("/assignment/status", response_model=List[dict])
async def course_homework_assignment_status(
    course_id: int,
    access_info: Dict = Depends(jwe_decode),
    db: AsyncSession = Depends(database),
):
    """
    查询学生在指定课程中的作业完成状态（仅限学生查询）

    参数：
        course_id: 课程ID
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        所有作业列表，包含完成状态和提交次数
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 查询课程信息
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar()

    # 检查课程是否存在
    if not course:
        return bad_request("Course not found")

    # 检查用户是否为该课程的学生
    result = await db.execute(
        select(CourseStudent).where(
            CourseStudent.course_id == course_id,
            CourseStudent.student_id == user_id,
        )
    )
    student = result.scalar()
    if not student:  # 必须是学生
        return forbidden("Only students can view their assignment status")

    # 获取课程的所有作业
    result = await db.execute(select(CourseHomeworkAssignment).where(CourseHomeworkAssignment.course_id == course_id))
    all_assignments = result.scalars().all()

    # 如果没有作业，直接返回空列表
    if not all_assignments:
        return ok(data=[])

    # 准备所有作业的状态信息
    status = []
    for assignment in all_assignments:
        # 查询该学生对该作业的所有提交
        result = await db.execute(
            select(CourseHomeworkSubmission).where(
                CourseHomeworkSubmission.homework_assignments_id == assignment.id,
                CourseHomeworkSubmission.student_id == user_id,
            )
        )
        submissions: List[CourseHomeworkSubmission] = result.scalars().all()

        # 获取作业详情并添加状态信息
        assignment_dict = assignment.dict()
        assignment_dict["is_overdue"] = True if assignment.deadline and datetime.now() > assignment.deadline else False  # 标记是否已过期
        assignment_dict["submission_count"] = len(submissions)  # 提交次数
        assignment_dict["is_completed"] = True if len(submissions) > 0 else False  # 是否已完成

        # 如果有提交，添加最新提交的评分信息
        if len(submissions) > 0:
            # 按创建时间倒序排序，获取最新提交
            assignment_dict["latest_submission_id"] = sorted(submissions, key=lambda x: x.created_at, reverse=True)[0].dict()
        else:
            assignment_dict["latest_submission_id"] = None

        status.append(assignment_dict)

    # 返回所有作业的状态信息
    return ok(data=status)


@api.put("/assignment", response_model=dict)
async def course_homework_assignment_update(
    body: CourseHomeworkAssignmentUpdate,
    access_info: Dict = Depends(jwe_decode),
    db: AsyncSession = Depends(database),
):
    """
    更新作业布置（仅教师）

    参数：
        body: 作业布置更新请求
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        更新后的作业布置对象
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 查询作业信息
    result = await db.execute(select(CourseHomeworkAssignment).where(CourseHomeworkAssignment.id == body.assignment_id))
    assignment = result.scalar()

    # 检查作业是否存在
    if not assignment:
        return bad_request("Assignment not found")

    # 查询课程信息
    result = await db.execute(select(Course).where(Course.id == assignment.course_id))
    course = result.scalar()

    # 检查用户是否为该课程的教师
    if course.teacher_id != user_id:
        return forbidden("Only course teacher can update assignments")

    # 更新课程目录条目ID列表 (如果提供)
    if body.course_directory_entry_ids is not None:
        # 验证文件条目是否存在且属于该课程
        for entry_id in body.course_directory_entry_ids:
            result = await db.execute(
                select(CourseDirectoryEntry, CourseDirectory)
                .join(
                    CourseDirectory,
                    CourseDirectoryEntry.course_directory_id == CourseDirectory.id,
                )
                .where(
                    CourseDirectoryEntry.id == entry_id,
                    CourseDirectory.course_id == course.id,
                )
            )
            entry_info = result.first()
            if not entry_info:
                return bad_request(f"Entry {entry_id} not found or not belong to this course")
        assignment.course_directory_entry_ids = body.course_directory_entry_ids

    # 更新其他字段 (如果提供)
    if body.title is not None:
        assignment.title = body.title
    if body.description is not None:
        assignment.description = body.description
    if body.deadline is not None:
        assignment.deadline = body.deadline

    # 更新时间戳
    assignment.updated_at = datetime.now()

    # 保存到数据库
    await db.commit()
    await db.refresh(assignment)

    return ok(data=assignment.dict())
