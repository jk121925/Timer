# your_project/routes/websocket_router.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import json
from core.connection_manager import manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, player_name: str = Query(...)):
    await websocket.accept()

    try:
        # 호스트 플레이어로 등록하여 새 그룹 생성
        group_name, player = await manager.register_player(websocket, player_name)

        await websocket.send_text(json.dumps({
            "status": "success",
            "action": "register_player",
            "group_name": group_name,
            "player_info": player.to_dict()
        }))

        while True:
            data = await websocket.receive_text()
            print(f"[WebSocket] Received from {player_name}: {data}")

    except WebSocketDisconnect:
        print(f"[WebSocket] Disconnected: {player_name}")
        removed_group = await manager.remove_connection_from_group(websocket)
        if removed_group:
            print(f"[WebSocket] Removed from group {removed_group}")
    except Exception as e:
        print(f"[WebSocket] Unexpected error: {e}")
