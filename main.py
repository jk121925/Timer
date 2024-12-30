# main.py
from fastapi import FastAPI
from routers import websocket, groups

app = FastAPI()

# 라우터 등록
app.include_router(websocket.router)
app.include_router(groups.router)


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app)
