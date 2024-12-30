# routers/groups.py
from fastapi import APIRouter, HTTPException
from typing import List, Dict
from core.connection_manager import manager, Client  # Client 클래스 임포트 추가
from models import ClientAddRequest, BroadcastMessage, ClientInfo

router = APIRouter()

@router.post("/groups/{group_name}/broadcast")
async def broadcast_message(group_name: str, message: BroadcastMessage):
    await manager.broadcast_to_group(group_name, message.message)
    return {"message": "메시지가 브로드캐스트되었습니다."}

@router.get("/groups", response_model=List[str])
async def list_groups():
    async with manager.lock:
        return list(manager.groups.keys())

@router.get("/groups/{group_name}/clients")
async def get_clients(group_name: str):
    async with manager.lock:
        if group_name not in manager.groups:
            raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
        clients = [client.to_dict() for client in manager.groups[group_name]]
        return {
            "group_name": group_name,
            "clients": clients
        }

@router.post("/groups/{group_name}/reorder")
async def reorder_group(group_name: str, new_order: List[str]):
    await manager.reorder_group(group_name, new_order)
    return {"message": "그룹 순서가 업데이트되었습니다."}

@router.post("/groups/{group_name}/start")
async def reorder_group(group_name: str):
    await manager.start_game(group_name)
    return manager.play_groups[group_name].to_dict()

@router.post("/groups/{group_name}/stop")
async def reorder_group(group_name: str):
    await manager.stop_game(group_name)
    return {"message": "게임 종료."}

@router.get("/groups/{group_name}/alert50")
async def alert50(group_name: str):
    if group_name not in manager.play_groups:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    await manager.broadcast_to_group(group_name,"alert50")

@router.get("/groups/{group_name}/alert70")
async def alert50(group_name: str):
    if group_name not in manager.play_groups:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    await manager.broadcast_to_group(group_name,"alert70")

@router.get("/groups/{group_name}/alert90")
async def alert50(group_name: str):
    if group_name not in manager.play_groups:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    await manager.broadcast_to_group(group_name,"alert90")

@router.get("/paly-groups/{group_name}/turn-over")
async def alert50(group_name: str):
    if group_name not in manager.play_groups:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    manager.play_groups[group_name].turn_over()
    return manager.play_groups[group_name].to_dict()

