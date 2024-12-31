from typing import Dict, List, Optional
from fastapi import WebSocket, HTTPException
import uuid
import asyncio
from .Timer import Timer

class Player:
    def __init__(self, websocket: WebSocket, player_name: str):
        self.websocket = websocket
        self.player_id = str(uuid.uuid4())
        self.player_name = player_name
        self.is_host = False

    def to_dict(self) -> dict:
        return {
            "player_id": self.player_id,
            "player_name": self.player_name,
            "is_host": self.is_host
        }

class Group:
    def __init__(self, host_player: Player, timer_hours=0, timer_minutes=0, timer_seconds=0):
        self.players: List[Player] = [host_player]
        self.host_player = host_player
        self.now_turn = 0
        self.is_active = False  # Indicates if the group is in active play mode
        self.timer = Timer(timer_hours, timer_minutes, timer_seconds)

    def add_player(self, player: Player):
        self.players.append(player)

    def remove_player(self, player_id: str):
        self.players = [player for player in self.players if player.player_id != player_id]

    def get_player_ids(self) -> List[str]:
        return [player.player_id for player in self.players]

    def to_dict(self):
        return {
            "host_player": self.host_player.to_dict(),
            "players": [player.to_dict() for player in self.players],
            "now_turn": self.now_turn,
            "is_active": self.is_active,
            "remaining_time": self.timer.get_remaining_time()
        }

    def start_game(self):
        if self.is_active:
            raise ValueError("Game is already active.")
        self.is_active = True
        self.now_turn = 0
        self.timer.start()

    def stop_game(self):
        if not self.is_active:
            raise ValueError("Game is not active.")
        self.is_active = False
        self.now_turn = 0
        self.timer.stop()

    def pause_game(self):
        if not self.is_active:
            raise ValueError("Game is not active.")
        self.is_active = False
        self.timer.pause()

    def turn_over(self):
        if not self.is_active:
            raise ValueError("Game is not active.")
        self.now_turn = (self.now_turn + 1) % len(self.players)

class ConnectionManager:
    def __init__(self):
        self.groups: Dict[str, Group] = {}
        self.lock = asyncio.Lock()

    async def register_player(self, websocket: WebSocket, player_name: str):
        async with self.lock:
            # Create a new host player and group
            host_player = Player(websocket, player_name)
            host_player.is_host = True

            group_name = f"group-{uuid.uuid4()}"
            self.groups[group_name] = Group(host_player)
            print(f"호스트 플레이어 '{host_player.player_id}'가 그룹 '{group_name}'을 생성했습니다.")
            return group_name, host_player

    async def join_group(self, host_player_id: str, guest_player_id: str):
        async with self.lock:
            # Find the host group by host player's ID
            host_group_name = None
            for g_name, group in self.groups.items():
                if group.host_player.player_id == host_player_id:
                    host_group_name = g_name
                    break

            if not host_group_name:
                raise HTTPException(status_code=404, detail="호스트 플레이어의 그룹을 찾을 수 없습니다.")

            # Find the guest player and their current group
            guest_player = None
            guest_group_name = None
            for g_name, group in self.groups.items():
                for player in group.players:
                    if player.player_id == guest_player_id:
                        guest_player = player
                        guest_group_name = g_name
                        break
                if guest_player:
                    break

            if not guest_player:
                raise HTTPException(status_code=404, detail="게스트 플레이어를 찾을 수 없습니다.")

            # Remove guest player from their current group
            if guest_group_name:
                guest_group = self.groups[guest_group_name]
                guest_group.remove_player(guest_player.player_id)
                print(f"플레이어 '{guest_player.player_id}'가 그룹 '{guest_group_name}'에서 제거되었습니다.")

                # Remove the group if empty
                if not guest_group.players:
                    del self.groups[guest_group_name]
                    print(f"그룹 '{guest_group_name}'이 비워져 삭제되었습니다.")

            # Add guest player to the host group
            guest_player.is_host = False
            host_group = self.groups[host_group_name]
            host_group.add_player(guest_player)
            print(f"플레이어 '{guest_player.player_id}'가 그룹 '{host_group_name}'에 추가되었습니다.")
            return host_group_name, guest_player

    async def reorder_group(self, group_name: str, new_order: List[str]) -> None:
        """Reorder the players in the group based on the given order of player IDs."""
        async with self.lock:
            if group_name not in self.groups:
                raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")

            group = self.groups[group_name]
            player_dict = {player.player_id: player for player in group.players}

            # 요청된 순서대로 플레이어 정렬
            reordered_players = []
            for player_id in new_order:
                if player_id in player_dict:
                    reordered_players.append(player_dict[player_id])
                else:
                    raise HTTPException(status_code=400, detail=f"잘못된 플레이어 ID: {player_id}")

            group.players = reordered_players
            print(f"그룹 '{group_name}'의 순서가 업데이트되었습니다: {[p.player_name for p in reordered_players]}.")

    async def remove_connection_from_group(self, websocket: WebSocket) -> Optional[str]:
        async with self.lock:
            for group_name, group in list(self.groups.items()):
                for player in group.players:
                    if player.websocket == websocket:
                        group.remove_player(player.player_id)
                        print(f"플레이어 '{player.player_id}'가 그룹 '{group_name}'에서 제거되었습니다.")

                        # Remove the group if empty
                        if not group.players:
                            del self.groups[group_name]
                            print(f"그룹 '{group_name}'이 비워져 삭제되었습니다.")
                        return group_name
            return None

    async def broadcast_to_group(self, group_name: str, message: str):
        async with self.lock:
            if group_name in self.groups:
                group = self.groups[group_name]
                for player in group.players:
                    if player.websocket:
                        try:
                            await player.websocket.send_text(message)
                        except Exception as e:
                            print(f"메시지 전송 실패: {e}")

    def get_players_in_group(self, group_name: str) -> List[dict]:
        if group_name in self.groups:
            return [player.to_dict() for player in self.groups[group_name].players]
        else:
            return []

    def start_game(self, group_name: str):
        if group_name not in self.groups:
            raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
        group = self.groups[group_name]
        try:
            group.start_game()
            print(f"게임이 그룹 '{group_name}'에서 시작되었습니다.")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    def stop_game(self, group_name: str):
        if group_name not in self.groups:
            raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
        group = self.groups[group_name]
        try:
            group.stop_game()
            print(f"게임이 그룹 '{group_name}'에서 종료되었습니다.")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    def pause_game(self, group_name: str):
        if group_name not in self.groups:
            raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
        group = self.groups[group_name]
        try:
            group.pause_game()
            print(f"게임이 그룹 '{group_name}'에서 일시 중지되었습니다.")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

# 싱글턴 패턴으로 인스턴스 생성
manager = ConnectionManager()
