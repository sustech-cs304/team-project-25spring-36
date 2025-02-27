from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from intellide.database.startup import startup as database_startup
from intellide.routers.entry import api as api_entry
from intellide.routers.share import api as api_share, ws as ws_share
from intellide.routers.user import api as api_user
from intellide.storage.startup import startup as storage_startup


# 定义声明周期函数
@asynccontextmanager
async def lifespan(_: FastAPI):
    # 程序启动
    await database_startup()
    await storage_startup()
    # 程序运行
    yield
    # 程序结束


# 服务端主程序
app = FastAPI(lifespan=lifespan, debug=True)

# 添加跨域中间件
app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建http路由
api = APIRouter(prefix="/api")
# 添加http路由
api.include_router(api_user)
api.include_router(api_entry)
api.include_router(api_share)

# 创建websocket路由
ws = APIRouter(prefix="/ws")
# 添加websocket路由
ws.include_router(ws_share)

# 添加路由
app.include_router(api)
app.include_router(ws)
