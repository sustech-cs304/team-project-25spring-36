from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from intellide.cache.startup import startup as cache_startup
from intellide.config import SERVER_HOST, SERVER_PORT
from intellide.database.startup import startup as database_startup
from intellide.docker.startup import startup as docker_startup
from intellide.routers.entry import api as api_entry
from intellide.routers.share import api as api_share, ws as ws_share
from intellide.routers.user import api as api_user
from intellide.storage.startup import startup as storage_startup
from intellide.utils.response import APIError, internal_server_error


# 定义生命周期函数
@asynccontextmanager
async def lifespan(_: FastAPI):
    # 程序启动
    await docker_startup()
    await cache_startup()
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


@app.exception_handler(APIError)
async def api_error_handler(_, error: APIError):
    return error.response()


@app.exception_handler(Exception)
async def exception_handler(_, error: Exception):
    return internal_server_error(message=str(error))


if __name__ == "__main__":
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
