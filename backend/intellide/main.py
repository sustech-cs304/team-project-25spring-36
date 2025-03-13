from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from intellide.config import SERVER_HOST, SERVER_PORT
from intellide.docker import startup_docker
from intellide.database import startup_database
from intellide.storage import startup_storage
from intellide.cache import startup_cache
from intellide.utils.response import APIError, internal_server_error
from intellide.routers import router


# 定义生命周期函数
@asynccontextmanager
async def lifespan(_: FastAPI):
    # 程序启动
    await startup_docker()
    await startup_cache()
    await startup_database()
    await startup_storage()
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

app.router(router)


@app.exception_handler(APIError)
async def api_error_handler(_, error: APIError):
    return error.response()


@app.exception_handler(Exception)
async def exception_handler(_, error: Exception):
    return internal_server_error(message=str(error))


if __name__ == "__main__":
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
