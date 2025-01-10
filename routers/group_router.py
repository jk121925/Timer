# your_project/routes/group_router.py

from fastapi import APIRouter, HTTPException
from typing import List
from core.connection_manager import manager

router = APIRouter()

@router.get("/", response_model=List[str])
async def list_groups():
    return list(manager.groups.keys())

@router.get("/{group_name}/players")
async def get_players_in_group(group_name: str):
    if group_name not in manager.groups:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    players = manager.get_players_in_group(group_name)
    return {"group_name": group_name, "players": players}

@router.post("/{group_name}/join")
async def join_group(group_name: str, host_player_id: str, guest_player_id: str):
    if group_name not in manager.groups:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    await manager.join_group(host_player_id, guest_player_id)
    return {"message": f"'{guest_player_id}' joined group '{group_name}'"}

@router.post("/{group_name}/reorder")
async def reorder_group(group_name: str, new_order_id: List[str]):
    if group_name not in manager.groups:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    await manager.reorder_group(group_name, new_order_id)
    return {"message": f"'{group_name}' player reorder"}

@router.get("/{group_name}")
async def get_play_group(group_name: str):
    if group_name not in manager.groups:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    return manager.groups[group_name].to_dict()

@router.post("/{group_name}/broadcast")
async def broadcast_message(group_name: str, message: str):
    if group_name not in manager.groups:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    await manager.broadcast_to_group(group_name, message)
    return {"message": "broadcast success"}
