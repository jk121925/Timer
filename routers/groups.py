from fastapi import APIRouter, HTTPException
from typing import List
from core.connection_manager import manager

router = APIRouter()

@router.post("/groups/{group_name}/broadcast")
async def broadcast_message(group_name: str, message: str):
    """
    Broadcast a message to all players in the group.
    """
    if group_name not in manager.groups:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    await manager.broadcast_to_group(group_name, message)
    return {"message": "메시지가 브로드캐스트되었습니다."}

@router.get("/groups", response_model=List[str])
async def list_groups():
    """
    List all group names.
    """
    return list(manager.groups.keys())

@router.get("/groups/{group_name}/players")
async def get_players_in_group(group_name: str):
    """
    Get all players in a specific group.
    """
    if group_name not in manager.groups:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    return {
        "group_name": group_name,
        "players": manager.get_players_in_group(group_name)
    }

@router.post("/groups/{group_name}/reorder")
async def reorder_group(group_name: str, new_order_id: List[str]):
    """
    Reorder players in a group by their player IDs.
    """
    if group_name not in manager.groups:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    await manager.reorder_group(group_name, new_order_id)
    return {"message": "그룹 순서가 업데이트되었습니다."}

@router.post("/play-groups/{group_name}/start")
async def start_game(group_name: str):
    """
    Start a game for a specific group.
    """
    if group_name not in manager.groups:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    play_group = manager.start_game(group_name)
    return play_group.to_dict()

@router.post("/play-groups/{group_name}/stop")
async def stop_game(group_name: str):
    """
    Stop a game for a specific group.
    """
    if group_name not in manager.play_groups:
        raise HTTPException(status_code=404, detail="플레이 중인 그룹을 찾을 수 없습니다.")
    manager.stop_game(group_name)
    return {"message": "게임이 종료되었습니다."}

@router.get("/play-groups/{group_name}/alert/{level}")
async def send_alert(group_name: str, level: int):
    """
    Send an alert to a group with the given level (50, 70, 90).
    """
    if group_name not in manager.play_groups:
        raise HTTPException(status_code=404, detail="플레이 중인 그룹을 찾을 수 없습니다.")
    if level not in [50, 70, 90]:
        raise HTTPException(status_code=400, detail="유효하지 않은 경고 수준입니다.")
    await manager.broadcast_to_group(group_name, f"alert{level}")
    return {"message": f"경고 {level}이 전송되었습니다."}

@router.post("/play-groups/{group_name}/turn-over")
async def turn_over(group_name: str):
    """
    Advance the turn for a specific play group.
    """
    if group_name not in manager.play_groups:
        raise HTTPException(status_code=404, detail="플레이 중인 그룹을 찾을 수 없습니다.")
    manager.play_groups[group_name].turn_over()
    return manager.play_groups[group_name].to_dict()

@router.get("/play-groups/{group_name}")
async def get_play_group(group_name: str):
    """
    Get details of a specific play group.
    """
    if group_name not in manager.play_groups:
        raise HTTPException(status_code=404, detail="플레이 중인 그룹을 찾을 수 없습니다.")
    return manager.play_groups[group_name].to_dict()
