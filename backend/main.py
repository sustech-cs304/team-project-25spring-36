from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.router.user import router as user
from backend.router.entry import router as entry

app = FastAPI()

# 添加跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加路由
app.include_router(user)
app.include_router(entry)
