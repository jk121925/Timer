# your_project/main.py

from fastapi import FastAPI
from routes.group_router import router as group_router
from routes.timer_router import router as timer_router
from routes.websocket_router import router as websocket_router

app = FastAPI()

# 그룹 관련 라우터
app.include_router(group_router, prefix="/group", tags=["group"])
# 타이머 관련 라우터
app.include_router(timer_router, prefix="/timer", tags=["timer"])
# WebSocket 라우터
app.include_router(websocket_router, tags=["websocket"])

# 실행: uvicorn your_project.main:app --reload
