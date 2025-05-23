import io
import json
import pickle
from typing import Dict, List

import y_py
from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
)
from fastapi.responses import Response, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from intellide.database import database
from intellide.database.model import (
    CourseCollaborativeDirectoryEntry,
    CourseCollaborativeDirectoryEntryEditHistory,
    UserRole,
)
from intellide.routers.course import (
    course_user_info,
)
from intellide.storage import (
    storage_name_create,
    storage_write_file,
    storage_read_file,
)
from intellide.utils.auth import jwe_decode
from intellide.utils.response import forbidden, ok, bad_request
from intellide.utils.websocket import WebSocketManager

# 创建课程共享可协作条目路由前缀
api = APIRouter(prefix="/course/collaborative")
ws = APIRouter(prefix="/course/collaborative")
manager = WebSocketManager()
editors: Dict[int, List[int]] = {}  # 跟踪每个文档的编辑者 {collab_id1: [user_id1, user_id2, ...], collab_id2: [user_id3, user_id4, ...], ...}
crdt_docs: Dict[int, y_py.YDoc] = {}  # 内存存储每个文档的crdt_doc {collab_id1: crdt_doc1, collab_id2: crdt_doc2, ...}


@api.post("")
async def course_collaborative_directory_entry_post(
    course_id: int,
    file: UploadFile = File(...),
    access_info: Dict = Depends(jwe_decode),
    db: AsyncSession = Depends(database),
):
    """
    创建课程共享可协作条目(仅文件，仅老师)

    参数:
        course_id: 课程ID
        file: 上传的文件
        access_info: 访问信息
        db: 数据库会话对象

    返回:
        course_collaborative_directory_entry_id: 协作条目ID
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 获取用户角色、课程、目录和条目信息
    user_role, course = await course_user_info(course_id=course_id, user_id=user_id, db=db)

    # 检查用户是否是课程教师
    if user_role != UserRole.TEACHER:
        return forbidden("Only teacher can create collaborative directory entry")

    # 创建协作条目
    storage_name = storage_name_create()
    file_content = await file.read()

    # 目前先支持文本的协作
    text_file_content = file_content.decode("utf-8", errors="replace")
    crdt_doc = y_py.YDoc()
    text = crdt_doc.get_text("text")
    
    # 创建事务并在事务中执行插入操作
    with crdt_doc.begin_transaction() as txn:
        text.insert(txn, 0, text_file_content)
    
    # 使用 y_py 的模块级函数进行序列化
    crdt_doc_bytes = y_py.encode_state_as_update(crdt_doc)
    await storage_write_file(
        storage_name=storage_name,
        content=crdt_doc_bytes,
    )
    course_collaborative_directory_entry = CourseCollaborativeDirectoryEntry(
        course_id=course_id,
        storage_name=storage_name,
    )
    db.add(course_collaborative_directory_entry)
    await db.commit()
    await db.refresh(course_collaborative_directory_entry)

    # 返回协作条目ID
    return ok(data={"course_collaborative_directory_entry_id": course_collaborative_directory_entry.id})


@api.get("")
async def course_collaborative_directory_entry_get(
    course_id: int,
    access_info: Dict = Depends(jwe_decode),
    db: AsyncSession = Depends(database),
):
    """
    获取课程共享可协作条目列表

    参数:
        course_id: 课程ID
        access_info: 访问信息
        db: 数据库会话对象

    返回:
        course_collaborative_directory_entries: 协作条目列表
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 获取用户角色、课程、目录和条目信息
    user_role, course = await course_user_info(course_id=course_id, user_id=user_id, db=db)

    # 检查用户是否是课程成员
    if user_role is None:
        return forbidden("Only users who have joined this course can get collaborative directory entries")

    # 获取协作条目
    course_collaborative_directory_entries = await db.execute(
        select(CourseCollaborativeDirectoryEntry).where(
            CourseCollaborativeDirectoryEntry.course_id == course_id,
        )
    )
    course_collaborative_directory_entries = course_collaborative_directory_entries.scalars().all()

    # 返回协作条目
    return ok(data=[course_collaborative_directory_entry.dict() for course_collaborative_directory_entry in course_collaborative_directory_entries])


@api.get("/history")
async def course_collaborative_directory_entry_edit_history_get(
    course_id: int,
    course_collaborative_directory_entry_id: int,
    access_info: Dict = Depends(jwe_decode),
    db: AsyncSession = Depends(database),
):
    """
    获取课程共享可协作条目编辑历史

    参数:
        course_id: 课程ID
        course_collaborative_directory_entry_id: 协作条目ID
        access_info: 访问信息
        db: 数据库会话对象

    返回:
        course_collaborative_directory_entry_edit_histories: 指定协作条目编辑历史列表
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 获取用户角色、课程、目录和条目信息
    user_role, course = await course_user_info(course_id=course_id, user_id=user_id, db=db)

    # 检查用户是否是课程成员
    if user_role is None:
        return forbidden("Only users who have joined this course can get collaborative directory entry edit history")

    # 获取协作条目历史
    course_collaborative_directory_entry_edit_histories = await db.execute(
        select(CourseCollaborativeDirectoryEntryEditHistory).where(
            CourseCollaborativeDirectoryEntryEditHistory.course_collaborative_directory_entry_id == course_collaborative_directory_entry_id,
        )
    )
    course_collaborative_directory_entry_edit_histories = course_collaborative_directory_entry_edit_histories.scalars().all()
    # 返回协作条目历史
    return ok(data=[course_collaborative_directory_entry_edit_history.dict() for course_collaborative_directory_entry_edit_history in course_collaborative_directory_entry_edit_histories])


@api.get("/download")
async def course_collaborative_directory_entry_download(
    course_id: int,
    course_collaborative_directory_entry_id: int,
    access_info: Dict = Depends(jwe_decode),
    db: AsyncSession = Depends(database),
):
    """
    下载课程共享可协作条目
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 获取用户角色、课程、目录和条目信息
    user_role, course = await course_user_info(course_id=course_id, user_id=user_id, db=db)

    # 检查用户是否是课程成员
    if user_role is None:
        return forbidden("Only users who have joined this course can download collaborative directory entry")

    # 获取协作条目
    course_collaborative_directory_entry = await db.execute(
        select(CourseCollaborativeDirectoryEntry).where(
            CourseCollaborativeDirectoryEntry.course_id == course_id,
            CourseCollaborativeDirectoryEntry.id == course_collaborative_directory_entry_id,
        )
    )
    course_collaborative_directory_entry = course_collaborative_directory_entry.scalar()
    if course_collaborative_directory_entry is None:
        return bad_request("no such collaborative directory entry")
    # 下载协作条目
    # 读取存储的字节
    print(f"[DEBUG] Downloading collab entry ID: {course_collaborative_directory_entry_id}, storage_name: {course_collaborative_directory_entry.storage_name}")
    update_bytes = await storage_read_file(course_collaborative_directory_entry.storage_name)
    print(f"[DEBUG] Read {len(update_bytes) if update_bytes else 0} bytes from storage for download.")
    
    ydoc = y_py.YDoc()
    try:
        if not update_bytes:
            print(f"[WARNING] update_bytes for doc ID {course_collaborative_directory_entry_id} is empty or None. YDoc will be empty.")
            # apply_update might fail with empty bytes, or do nothing.
            # If it's None, it will definitely fail. Let's ensure it's bytes.
            update_bytes = b'' 
        y_py.apply_update(ydoc, update_bytes)
        print(f"[DEBUG] Successfully applied update to YDoc for download (ID: {course_collaborative_directory_entry_id}).")
    except Exception as e:
        print(f"[ERROR] Failed to apply update to YDoc for download (ID: {course_collaborative_directory_entry_id}): {e}")
        import traceback
        print(traceback.format_exc())
        raise 
        
    ytext_obj = ydoc.get_text("text")
    if ytext_obj is None:
        print(f"[ERROR] ydoc.get_text('text') returned None for doc ID {course_collaborative_directory_entry_id} during download.")
        ytext_content = "" # Default to empty string
    else:
        # 使用 str() 来获取 YText 的内容
        ytext_content = str(ytext_obj)
        if not isinstance(ytext_content, str):
            print(f"[ERROR] str(ytext_obj) did not return a string (got {type(ytext_content)}) for doc ID {course_collaborative_directory_entry_id}. Content: {str(ytext_content)[:200]}")
            
    print(f"[DEBUG] Extracted text content for download (length: {len(ytext_content)}). Preview: {ytext_content[:200]}...")

    file_name = f"{course_collaborative_directory_entry.storage_name}.txt"
    
    try:
        content_bytes = ytext_content.encode("utf-8")
        print(f"[DEBUG] Encoded ytext_content to {len(content_bytes)} bytes for Response (download).")
        # 使用 Response 而不是 FileResponse
        return Response(
            content=content_bytes,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={file_name}"},
        )
    except Exception as e:
        print(f"[ERROR] Failed to create or return Response for download (ID: {course_collaborative_directory_entry_id}): {e}")


@api.delete("")
async def course_collaborative_directory_entry_delete(
    course_id: int,
    course_collaborative_directory_entry_id: int,
    access_info: Dict = Depends(jwe_decode),
    db: AsyncSession = Depends(database),
):
    """
    删除课程共享可协作条目(仅老师)

    参数:
        course_id: 课程ID
        course_collaborative_directory_entry_id: 协作条目ID
        access_info: 访问信息
        db: 数据库会话对象
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 获取用户角色、课程、目录和条目信息
    user_role, course = await course_user_info(course_id=course_id, user_id=user_id, db=db)

    # 检查用户是否是课程教师
    if user_role != UserRole.TEACHER:
        return forbidden("Only teacher can delete collaborative directory entry")

    # 获取协作条目
    course_collaborative_directory_entry = await db.execute(
        select(CourseCollaborativeDirectoryEntry).where(
            CourseCollaborativeDirectoryEntry.course_id == course_id,
            CourseCollaborativeDirectoryEntry.id == course_collaborative_directory_entry_id,
        )
    )
    course_collaborative_directory_entry = course_collaborative_directory_entry.scalar()
    if course_collaborative_directory_entry is None:
        return bad_request("no such collaborative directory entry")
    # 删除协作条目
    await db.delete(course_collaborative_directory_entry)
    await db.commit()

    # 返回成功响应
    return ok()


async def broadcast_editors(course_collaborative_directory_entry_id: int):
    """
    广播编辑者更新
    """
    keys = (course_collaborative_directory_entry_id,)
    if course_collaborative_directory_entry_id in editors:
        await manager.broadcast_json(keys=keys, content={"type": "user_updated", "editors": list(editors[course_collaborative_directory_entry_id])})
    else:
        await manager.broadcast_json(keys=keys, content={"type": "user_updated", "editors": []})



async def add_user_to_editors(collab_id: int, user_id: int):
    """
    添加用户到编辑者列表
    """
    if collab_id not in editors:
        editors[collab_id] = []
    editors[collab_id].append(user_id)
    await broadcast_editors(collab_id)


async def remove_user_from_editors(collab_id: int, user_id: int):
    """
    从编辑者列表中移除用户
    """
    if collab_id in editors:
        editors[collab_id].remove(user_id)
        if not editors[collab_id]:
            del editors[collab_id]
        await broadcast_editors(collab_id)


async def get_crdt_doc_from_storage_or_memory(
    course_collaborative_directory_entry_id: int,
    entry: CourseCollaborativeDirectoryEntry,
):
    """
    获取协作条目CRDT文档
    """
    # 如果CRDT文档在内存中，则返回内存中的CRDT文档, 否则从存储中读取CRDT文档
    if course_collaborative_directory_entry_id not in crdt_docs:
        print(f"[DEBUG] CRDT Doc {course_collaborative_directory_entry_id} not in memory. Loading from storage: {entry.storage_name}")
        update_bytes = await storage_read_file(entry.storage_name)
        print(f"[DEBUG] Read {len(update_bytes) if update_bytes else 0} bytes from storage for doc {course_collaborative_directory_entry_id}.")
        crdt_doc = y_py.YDoc()
        try:
            # 使用 y_py 的方法进行反序列化
            y_py.apply_update(crdt_doc, update_bytes)
            print(f"[DEBUG] Successfully applied update to YDoc {course_collaborative_directory_entry_id} from storage.")
        except Exception as e:
            print(f"[ERROR] Failed to apply update to YDoc {course_collaborative_directory_entry_id} from storage: {e}")
            # 考虑是否应该在这里抛出异常，或者返回一个空的/错误状态的文档
            # 目前，如果加载失败，后续代码可能会因为crdt_doc未正确初始化而出错
            raise # 暂时重新抛出，以便追踪问题
        crdt_docs[course_collaborative_directory_entry_id] = crdt_doc
    else:
        print(f"[DEBUG] CRDT Doc {course_collaborative_directory_entry_id} found in memory.")
    return crdt_docs[course_collaborative_directory_entry_id]


@ws.websocket("/join")
async def collaborative_join(
    websocket: WebSocket,
    course_id: int,
    course_collaborative_directory_entry_id: int,
    access_info: Dict = Depends(jwe_decode),
    db: AsyncSession = Depends(database),
):
    """
    加入协作编辑会话
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 验证用户权限
    user_role, course = await course_user_info(course_id=course_id, user_id=user_id, db=db)
    if user_role is None:
        await websocket.close(code=1008, reason="无权限访问此课程")
        return

    # 验证协作条目存在
    entry_result = await db.execute(
        select(CourseCollaborativeDirectoryEntry).where(
            CourseCollaborativeDirectoryEntry.id == course_collaborative_directory_entry_id,
            CourseCollaborativeDirectoryEntry.course_id == course_id,
        )
    )
    entry = entry_result.scalar()
    if entry is None:
        await websocket.close(code=1008, reason="协作条目不存在")
        return

    # 接受WebSocket连接
    try:
        await websocket.accept()
    except (WebSocketException, WebSocketDisconnect):
        await websocket.close(code=1008, reason="无法接受WebSocket连接")
        return

    # 使用WebSocketManager添加连接
    # 使用course_collaborative_directory_entry_id作为分组键，用户ID作为连接标识符
    manager.add(
        keys=(course_collaborative_directory_entry_id,),
        identifier=user_id,
        websocket=websocket,
    )

    # 先获取并发送初始内容
    crdt_doc = await get_crdt_doc_from_storage_or_memory(course_collaborative_directory_entry_id, entry)
    crdt_text = crdt_doc.get_text("text")
    await websocket.send_json(
        {
            "type": "content",
            "content": str(crdt_text),
            "user_id": user_id,
        }
    )

    # 然后将当前用户添加到编辑者列表, 并广播编辑者更新
    await add_user_to_editors(course_collaborative_directory_entry_id, user_id)

    try:
        # 处理消息
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # 根据消息类型处理
            if message.get("type") == "edit":
                # 处理内容更新
                operation = message.get("operation")
                position = message.get("position")
                content = message.get("content", "")

                if operation == "insert":
                    # 创建事务并在事务中执行插入操作
                    with crdt_doc.begin_transaction() as txn:
                        crdt_text.insert(txn, position, content)
                elif operation == "delete":
                    # 删除操作也应该在事务中执行
                    with crdt_doc.begin_transaction() as txn:
                        # delete方法通常需要 txn, index, length
                        crdt_text.delete(txn, position, len(content))

                # 广播更新
                await manager.broadcast_json(
                    keys=(course_collaborative_directory_entry_id,),
                    content={
                        "type": "content",
                        "content": str(crdt_text),
                        "user_id": user_id,
                    },
                )
                # 记录编辑历史
                edit_history = CourseCollaborativeDirectoryEntryEditHistory(
                    course_collaborative_directory_entry_id=course_collaborative_directory_entry_id,
                    editor_id=user_id,
                    operation=operation,
                    position=position,
                    content=content,
                )
                db.add(edit_history)
                await db.commit()

    except (WebSocketDisconnect, WebSocketException):
        await websocket.close()
    finally:
        crdt_doc_bytes = y_py.encode_state_as_update(crdt_doc)
        await storage_write_file(
            storage_name=entry.storage_name,
            content=crdt_doc_bytes,
        )
        manager.remove(keys=(course_collaborative_directory_entry_id,), identifier=user_id)
        await remove_user_from_editors(course_collaborative_directory_entry_id, user_id)

        # 如果发现编辑者列表为空，则从内存中删除CRDT文档
        if course_collaborative_directory_entry_id not in editors:
            del crdt_docs[course_collaborative_directory_entry_id]

        await websocket.close(code=1008, reason="用户离开协作编辑会话")
