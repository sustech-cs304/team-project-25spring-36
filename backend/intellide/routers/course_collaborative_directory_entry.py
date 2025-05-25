from datetime import datetime
import io
import json
import pickle
from typing import Dict, List

from sqlalchemy import update
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
last_updated_at_dict: Dict[int, datetime] = {}  # 内存存储每个文档的last_updated_at {collab_id1: time1, collab_id2: time2, ...}
last_updated_by_dict: Dict[int, int] = {}  # 内存存储每个文档的last_updated_by {collab_id1: user_id1, collab_id2: user_id2, ...}


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
        last_updated_by=user_id,
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
    update_bytes = await storage_read_file(course_collaborative_directory_entry.storage_name)
    
    ydoc = y_py.YDoc()
    try:
        if not update_bytes:
            update_bytes = b'' 
        y_py.apply_update(ydoc, update_bytes)
    except Exception as e:
        raise 
        
    ytext_obj = ydoc.get_text("text")
    if ytext_obj is None:
        ytext_content = "" # Default to empty string
    else:
        # 使用 str() 来获取 YText 的内容
        ytext_content = str(ytext_obj)           
    file_name = f"{course_collaborative_directory_entry.storage_name}.txt"

    try:
        content_bytes = ytext_content.encode("utf-8")
        # 使用 Response 而不是 FileResponse
        return Response(
            content=content_bytes,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={file_name}"},
    )
    except Exception as e:
        raise

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
    # 客户端可以从user_updated消息中获得当前的编辑者列表
    keys = (course_collaborative_directory_entry_id,)
    if course_collaborative_directory_entry_id in editors:
        await manager.broadcast_json(
            keys=keys,
            content={
                "type": "user_updated",
                "editors": list(editors[course_collaborative_directory_entry_id])
            }
        )
    else:
        await manager.broadcast_json(
            keys=keys, 
            content={
                "type": "user_updated",
                "editors": []
            }
        )



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
        update_bytes = await storage_read_file(entry.storage_name)
        crdt_doc = y_py.YDoc()
        try:
            # 使用 y_py 的方法进行反序列化
            y_py.apply_update(crdt_doc, update_bytes)
        except Exception as e:
            raise 
        crdt_docs[course_collaborative_directory_entry_id] = crdt_doc
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

    # ------------------------------------------------------------
    # 客户端使用说明：
    # ----------------------------准备----------------------------
    # 客户端需要使用Yjs库，进入文档时，使用Y.Doc()创建一个空的ydoc实例
    # 写两个用于转换Uint8Array到十六进制和十六进制到Uint8Array的函数
    #
    # 客户端需要在刚连接时，和定期刷新时发送sync操作，请求与服务端同步文档内容
    # 需要发送的json格式如下：
    # {
    #     "type": "sync",
    #     "state_vector": state_vector_bytes_hex,
    # }
    # state_vector_bytes_hex 是客户端当前的CRDT状态向量
    # 使用 Y.encodeStateVector(客户端的ydoc)，并将其转为十六进制 获得
    # ----------------------------接收----------------------------
    # 客户端如果接受到服务端发送的任何的update消息，都应该从中获取同步更新包
    # 接收到的json格式如下：
    # {
    #     "type": "update",
    #     "update": update_bytes_hex,
    #     "user_id": user_id,
    #     "time": time,
    # }
    # update_bytes_hex 是服务端生成的同步更新包
    # 客户端随后应该将这个更新包应用到自己的CRDT文档
    # 即Y.applyUpdate(客户端的ydoc, 转Uint8Array(update_bytes_hex))
    # user_id和time应该被用来显示“xxx最后于xx:xx编辑”到前端上
    # ----------------------------发送-----------------------------
    # 当客户端更改文档时，客户端需要发送增量更新给服务器
    # 需要发送的json格式如下：
    # {
    #     "type": "update",
    #     "update": update_bytes_hex,
    # }
    # 比如Yjs生成了一个二进制更新 `delta_bytes`（通过监听Yjs文档的update事件）
    # 需要发送的update_bytes_hex就是转十六进制(delta_bytes)



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
    
    if last_updated_at_dict.get(course_collaborative_directory_entry_id) is None:
        last_updated_at_dict[course_collaborative_directory_entry_id] = entry.last_updated_at
    if last_updated_by_dict.get(course_collaborative_directory_entry_id) is None:
        last_updated_by_dict[course_collaborative_directory_entry_id] = entry.last_updated_by

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

    # 获取主CRDT文档
    master_crdt_doc = await get_crdt_doc_from_storage_or_memory(course_collaborative_directory_entry_id, entry)
    
    # 将当前用户添加到编辑者列表, 并广播编辑者更新
    await add_user_to_editors(course_collaborative_directory_entry_id, user_id)

    try:
        # 处理消息
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            # 根据消息类型处理
            if message.get("type") == "sync":
                # 获得客户端当前的状态向量
                client_state_vector_bytes = bytes.fromhex(message.get("state_vector", ""))
                # 生成针对该客户端的同步更新包
                sync_update = y_py.encode_state_as_update(master_crdt_doc, client_state_vector_bytes)
                
                # 发送同步更新包给客户端
                await websocket.send_json({
                    "type": "update",
                    "update": sync_update.hex(),
                    "user_id": last_updated_by_dict[course_collaborative_directory_entry_id],
                    "time": last_updated_at_dict[course_collaborative_directory_entry_id].strftime("%Y-%m-%d %H:%M:%S"),
                })

            elif message.get("type") == "update":
                update_bytes_hex = message.get("update", "")
                update_bytes = bytes.fromhex(update_bytes_hex)
                # 将更新应用到主CRDT文档
                y_py.apply_update(master_crdt_doc, update_bytes)
                last_updated_at_dict[course_collaborative_directory_entry_id] = datetime.now()
                last_updated_by_dict[course_collaborative_directory_entry_id] = user_id
                
                # 广播这个更新给所有客户端（包括发送者，这不要紧，因为CRDT会自动忽略处理重复的更新）
                await manager.broadcast_json(
                    keys=(course_collaborative_directory_entry_id,),
                    content={
                        "type": "update",
                        "update": update_bytes.hex(),
                        "user_id": last_updated_by_dict[course_collaborative_directory_entry_id],
                        "time": last_updated_at_dict[course_collaborative_directory_entry_id].strftime("%Y-%m-%d %H:%M:%S"),
                    },
                )

    except (WebSocketDisconnect, WebSocketException):
        await websocket.close()
    finally:
        # 保存最新的CRDT文档状态到存储
        crdt_doc_bytes = y_py.encode_state_as_update(master_crdt_doc)
        await storage_write_file(
            storage_name=entry.storage_name,
            content=crdt_doc_bytes,
        )

        # 更新last_updated_by到数据库（last_updated_at会自动更新）
        await db.execute(
            update(CourseCollaborativeDirectoryEntry).where(
                CourseCollaborativeDirectoryEntry.id == course_collaborative_directory_entry_id,
            ).values(last_updated_by=user_id)
        )
        await db.commit()
        
        # 清理连接和编辑者列表
        manager.remove(keys=(course_collaborative_directory_entry_id,), identifier=user_id)
        await remove_user_from_editors(course_collaborative_directory_entry_id, user_id)

        # 如果发现编辑者列表为空，则从内存中删除CRDT文档
        if course_collaborative_directory_entry_id not in editors:
            if course_collaborative_directory_entry_id in crdt_docs:
                del crdt_docs[course_collaborative_directory_entry_id]

        await websocket.close(code=1008, reason="用户离开协作编辑会话")
