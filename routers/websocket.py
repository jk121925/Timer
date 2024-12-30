# routers/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from typing import Optional
import json
from core.connection_manager import manager
from models import ClientInfo
import uuid

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    group: Optional[str] = Query(None),
    client_name: str = Query()
):
    await websocket.accept()
    try:
        if group:
            # Attempt to join the existing group
            try:
                group_name, client = await manager.join_group(group, websocket, client_name)
                await websocket.send_text(json.dumps({
                    "status": "success",
                    "action": "join_group",
                    "group_name": group_name,
                    "client_info": client.to_dict()  # 이미 dict 형태로 변경됨
                }))
            except HTTPException as e:
                if e.status_code == 404:
                    # Create new group if it doesn't exist
                    group_name, client = await manager.create_group(group, websocket, client_name)
                    await websocket.send_text(json.dumps({
                        "status": "success",
                        "action": "create_group",
                        "group_name": group_name,
                        "client_info": client.to_dict()  # 이미 dict 형태로 변경됨
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "status": "error",
                        "action": "join_group",
                        "message": e.detail
                    }))
                    await websocket.close()
                    return
        else:
            # Create a unique group name
            unique_group_name = f"group-{uuid.uuid4()}"
            group_name, client = await manager.create_group(unique_group_name, websocket, client_name)
            await websocket.send_text(json.dumps({
                "status": "success",
                "action": "create_group",
                "group_name": group_name,
                "client_info": client.to_dict()  # 이미 dict 형태로 변경됨
            }))

        # Keep the connection alive, but do not process incoming messages
        while True:
            try:
                # Wait for incoming messages, but ignore them
                data = await websocket.receive_text()
                # For passive sending, just ignore
                pass
            except WebSocketDisconnect:
                raise
            except Exception as e:
                print(f"예외 발생: {e}")
                raise

    except WebSocketDisconnect:
        group_name = await manager.remove_connection_from_group(websocket)
        if group_name:
            await manager.broadcast_to_group(group_name, f"클라이언트가 그룹 '{group_name}'에서 나갔습니다.")
    except Exception as e:
        print(f"예외 발생: {e}")
        group_name = await manager.remove_connection_from_group(websocket)
        if group_name:
            await manager.broadcast_to_group(group_name, f"클라이언트가 그룹 '{group_name}'에서 오류로 인해 나갔습니다.")
        await websocket.close()
