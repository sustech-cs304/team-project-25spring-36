from fastapi import APIRouter

from intellide.routers.course import api as course_api
from intellide.routers.course_chat import ws as course_chat_ws
from intellide.routers.course_directory import api as course_directory_api
from intellide.routers.course_directory_entry import api as course_directory_entry_api
from intellide.routers.course_student import api as course_student_api
from intellide.routers.user import api as user_api

# 创建 WebSocket 路由
router_ws = APIRouter(prefix="/ws")

router_ws.include_router(course_chat_ws)

# 创建 API 路由
router_api = APIRouter(prefix="/api")

router_api.include_router(course_api)
router_api.include_router(course_directory_api)
router_api.include_router(course_directory_entry_api)
router_api.include_router(course_student_api)
router_api.include_router(user_api)

# 创建主路由
router = APIRouter()

router.include_router(router_ws)
router.include_router(router_api)
