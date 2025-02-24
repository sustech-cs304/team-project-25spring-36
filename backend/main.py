from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from backend.router.user import api as api_user
from backend.router.entry import api as api_entry
from backend.router.share import api as api_share, ws as ws_share

app = FastAPI()

# 添加跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api")
ws = APIRouter(prefix="/ws")

# 添加路由
api.include_router(api_user)
api.include_router(api_entry)
api.include_router(api_share)

ws.include_router(ws_share)

app.include_router(api)
app.include_router(ws)
