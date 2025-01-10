# your_project/routes/timer_router.py

from fastapi import APIRouter, HTTPException
from core.connection_manager import manager

router = APIRouter()

@router.post("/set-time/{group_name}")
async def set_time(group_name: str, h: int, m: int, s: int):
    if group_name not in manager.groups:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    manager.groups[group_name].set_time(h, m, s)
    return {"message": f"Set timer for '{group_name}' to {h}:{m}:{s}"}

@router.post("/start/{group_name}")
async def start_game(group_name: str):
    if group_name not in manager.groups:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    group = await manager.start_game(group_name)
    return {"message": f"Game started in '{group_name}'", "group": group.to_dict()}

@router.post("/stop/{group_name}")
async def stop_game(group_name: str):
    if group_name not in manager.groups:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    await manager.stop_game(group_name)
    return {"message": f"Game stopped in '{group_name}'"}

@router.post("/pause/{group_name}")
async def pause_game(group_name: str):
    if group_name not in manager.groups:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    await manager.pause_game(group_name)
    return {"message": f"Game paused in '{group_name}'"}

@router.post("/resume/{group_name}")
async def resume_game(group_name: str):
    if group_name not in manager.groups:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    await manager.resume_game(group_name)
    return {"message": f"Game resumed in '{group_name}'"}

@router.post("/turn-over/{group_name}")
async def turn_over(group_name: str):
    if group_name not in manager.groups:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    group = await manager.turn_over(group_name)
    return {"message": f"Turn over in '{group_name}'", "group": group.to_dict()}
