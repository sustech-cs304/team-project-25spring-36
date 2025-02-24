from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from backend.router.user import api as api_user
from backend.router.entry import api as api_entry
from backend.router.share import api as api_share, ws as ws_share

# 创建http路由
api = APIRouter(prefix="/api")
# 创建websocket路由
ws = APIRouter(prefix="/ws")

# 添加http路由
api.include_router(api_user)
api.include_router(api_entry)
api.include_router(api_share)

# 添加websocket路由
ws.include_router(ws_share)

# 服务端主程序
app = FastAPI(debug=True)

# 添加跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加路由
app.include_router(api)
app.include_router(ws)
