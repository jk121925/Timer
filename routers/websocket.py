from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import json
from core.connection_manager import manager  # Import the connection manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, player_name: str = Query(...)):
    await websocket.accept()

    try:
        # Register the player through the connection manager
        group_name, player = await manager.register_player(websocket, player_name)

        # Send confirmation to the client
        await websocket.send_text(json.dumps({
            "status": "success",
            "action": "register_player",
            "group_name": group_name,
            "player_info": player.to_dict()
        }))

    except WebSocketDisconnect:
        # Remove the WebSocket connection from the group on disconnect
        group_name = await manager.remove_connection_from_group(websocket)
        if group_name:
            print(f"Connection for player in group '{group_name}' has been removed.")
