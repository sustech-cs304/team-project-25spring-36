from fastapi import FastAPI
from backend.router.user import router as user
from backend.router.entry import router as entry

app = FastAPI()

app.include_router(user)
app.include_router(entry)

