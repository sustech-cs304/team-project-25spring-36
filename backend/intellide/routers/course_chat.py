from typing import Dict

from fastapi import APIRouter, Depends
from fastapi import WebSocket, WebSocketDisconnect, WebSocketException
from sqlalchemy.ext.asyncio import AsyncSession

from intellide.database import database
from intellide.routers.course import course_user_info
from intellide.utils.auth import jwe_decode
from intellide.utils.websocket import WebSocketManager

ws = APIRouter(prefix="/course/chat")

manager = WebSocketManager()


@ws.websocket("/{course_id}")
async def course_chat(
        websocket: WebSocket,
        course_id: int,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    """
    课程聊天 WebSocket

    参数：
        websocket: WebSocket对象
        course_id: 课程ID
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象
    """
    user_id, user_username = access_info["user_id"], access_info["user_username"]
    # 获取用户角色和课程信息
    role, course = await course_user_info(
        course_id=course_id,
        user_id=user_id,
        db=db,
    )
    # 如果用户没有权限，关闭 WebSocket 连接
    if role is None:
        await websocket.close(code=1008)
        return
    # 接受 WebSocket 连接
    try:
        await websocket.accept()
    except (WebSocketException, WebSocketDisconnect):
        await websocket.close(code=1008)
        return
    # 添加 WebSocket 连接到管理器
    keys = (course_id,)
    manager.add(
        keys=keys,
        identifier=user_id,
        websocket=websocket
    )
    # 处理 WebSocket 消息
    try:
        while True:
            await manager.broadcast_json(
                keys=keys,
                content={
                    "user_id": user_id,
                    "user_username": user_username,
                    "data": await websocket.receive_json(),
                }
            )
    # 移除 WebSocket 连接
    except (WebSocketDisconnect, WebSocketException):
        manager.remove(
            keys=keys,
            identifier=user_id
        )
