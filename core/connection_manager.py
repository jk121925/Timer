# your_project/core/connection_manager.py

import uuid
import asyncio
from typing import Dict, List, Optional
from fastapi import WebSocket, HTTPException

from core.player import Player
from core.group import Group

class ConnectionManager:
    def __init__(self):
        self.groups: Dict[str, Group] = {}
        self.lock = asyncio.Lock()

    async def broadcast_to_group(self, group_name: str, message: str):
        """동일한 그룹 내 모든 플레이어에게 메시지 전송"""
        async with self.lock:
            if group_name not in self.groups:
                return
            group = self.groups[group_name]
            for p in group.players:
                if p.websocket:
                    try:
                        await p.websocket.send_text(message)
                    except Exception as e:
                        print(f"[ConnectionManager] Broadcast failed: {e}")

    def _make_broadcast_callback(self):
        """Group에 주입할 콜백 함수. group_name, message -> await broadcast_to_group(group_name, message)"""
        async def broadcast_cb(group_name: str, msg: str):
            await self.broadcast_to_group(group_name, msg)
        return broadcast_cb

    async def register_player(self, websocket: WebSocket, player_name: str):
        """
        새로운 그룹을 생성하고 호스트 플레이어 등록
        """
        async with self.lock:
            host_player = Player(websocket, player_name)
            host_player.is_host = True

            group_name = f"group-{uuid.uuid4()}"

            broadcast_cb = self._make_broadcast_callback()
            new_group = Group(
                group_name=group_name,
                host_player=host_player,
                broadcast_callback=broadcast_cb,
                h=0, m=0, s=30   # 기본 30초 타이머 예시
            )
            self.groups[group_name] = new_group

            print(f"[ConnectionManager] New group '{group_name}' created by '{player_name}'")
            return group_name, host_player

    async def join_group(self, host_player_id: str, guest_player_id: str):
        """
        호스트 그룹을 찾은 뒤, 게스트 플레이어를 그 그룹으로 이동
        """
        async with self.lock:
            host_group_name = None
            for g_name, grp in self.groups.items():
                if grp.host_player.player_id == host_player_id:
                    host_group_name = g_name
                    break
            if not host_group_name:
                raise HTTPException(status_code=404, detail="호스트 그룹을 찾을 수 없습니다.")

            guest_player = None
            guest_group_name = None
            for g_name, grp in self.groups.items():
                for p in grp.players:
                    if p.player_id == guest_player_id:
                        guest_player = p
                        guest_group_name = g_name
                        break
                if guest_player:
                    break
            if not guest_player:
                raise HTTPException(status_code=404, detail="게스트 플레이어를 찾을 수 없습니다.")

            # 기존 그룹에서 제거
            if guest_group_name:
                old_grp = self.groups[guest_group_name]
                old_grp.remove_player(guest_player_id)
                print(f"[ConnectionManager] Player '{guest_player_id}' removed from '{guest_group_name}'")
                if not old_grp.players:
                    del self.groups[guest_group_name]
                    print(f"[ConnectionManager] Group '{guest_group_name}' removed (empty)")

            # 호스트 그룹에 추가
            guest_player.is_host = False
            host_grp = self.groups[host_group_name]
            host_grp.add_player(guest_player)
            print(f"[ConnectionManager] Player '{guest_player_id}' joined '{host_group_name}'")

            return host_group_name, guest_player

    async def reorder_group(self, group_name: str, new_order: List[str]) -> None:
        """그룹 플레이어 순서를 new_order 순으로 재정렬"""
        async with self.lock:
            if group_name not in self.groups:
                raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")

            group = self.groups[group_name]
            player_dict = {p.player_id: p for p in group.players}

            reordered = []
            for pid in new_order:
                if pid not in player_dict:
                    raise HTTPException(status_code=400, detail=f"잘못된 플레이어 ID: {pid}")
                reordered.append(player_dict[pid])

            group.players = reordered
            print(f"[ConnectionManager] Group '{group_name}' reorder -> {[p.player_name for p in reordered]}")

    async def remove_connection_from_group(self, websocket: WebSocket) -> Optional[str]:
        """WebSocket이 끊긴 플레이어를 소속 그룹에서 제거"""
        async with self.lock:
            for g_name, grp in list(self.groups.items()):
                for p in grp.players:
                    if p.websocket == websocket:
                        grp.remove_player(p.player_id)
                        print(f"[ConnectionManager] Player '{p.player_id}' removed from '{g_name}'")
                        if not grp.players:
                            del self.groups[g_name]
                            print(f"[ConnectionManager] Group '{g_name}' removed (empty)")
                        return g_name
            return None

    def get_all_player(self):
        """모든 플레이어 조회"""
        players = []
        for grp in self.groups.values():
            players.extend(grp.players)
        return players

    def get_players_in_group(self, group_name: str):
        if group_name in self.groups:
            return [p.to_dict() for p in self.groups[group_name].players]
        return []

    # --- 비동기로 그룹의 메서드를 호출 ---

    async def start_game(self, group_name: str):
        if group_name not in self.groups:
            raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
        group = self.groups[group_name]
        await group.start_game()
        print(f"[ConnectionManager] start_game -> '{group_name}'")
        return group

    async def stop_game(self, group_name: str):
        if group_name not in self.groups:
            raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
        group = self.groups[group_name]
        await group.stop_game()
        print(f"[ConnectionManager] stop_game -> '{group_name}'")

    async def pause_game(self, group_name: str):
        if group_name not in self.groups:
            raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
        group = self.groups[group_name]
        await group.pause_game()
        print(f"[ConnectionManager] pause_game -> '{group_name}'")

    async def resume_game(self, group_name: str):
        if group_name not in self.groups:
            raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
        group = self.groups[group_name]
        await group.resume_game()
        print(f"[ConnectionManager] resume_game -> '{group_name}'")

    async def turn_over(self, group_name: str):
        if group_name not in self.groups:
            raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
        group = self.groups[group_name]
        await group.turn_over()
        print(f"[ConnectionManager] turn_over -> '{group_name}'")
        return group

manager = ConnectionManager()  # 싱글턴 인스턴스
