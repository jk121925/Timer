# your_project/core/group.py

import json
import asyncio
from typing import List, Callable
from core.player import Player
from core.async_timer import AsyncTimer

class Group:
    def __init__(
        self,
        group_name: str,
        host_player: Player,
        broadcast_callback: Callable[[str, str], asyncio.Future],
        h=0,
        m=0,
        s=0
    ):
        self.group_name = group_name
        self.players: List[Player] = [host_player]
        self.host_player = host_player
        self.now_turn = 0
        self.is_active = False

        # 메시지 전송을 위한 콜백 함수 (manager에서 주입)
        self.broadcast_callback = broadcast_callback

        # 비동기 타이머
        self.timer = AsyncTimer(
            h, m, s,
            on_tick_callback=self.broadcast_remaining_time,
            on_timeout_callback=self.on_timer_timeout
        )

    async def broadcast_remaining_time(self, remaining_seconds: int):
        """타이머 tick 콜백 (비동기)"""
        msg = json.dumps({
            "action": "update_timer",
            "now_turn": self.now_turn,
            "remaining_seconds": remaining_seconds
        })
        await self.broadcast_callback(self.group_name, msg)

    async def on_timer_timeout(self):
        """타이머가 0초 도달 시 (비동기)"""
        print(f"[Group {self.group_name}] Timer expired, switching turn.")
        await self.turn_over()

    def add_player(self, player: Player):
        self.players.append(player)

    def remove_player(self, player_id: str):
        self.players = [p for p in self.players if p.player_id != player_id]

    def set_time(self, h: int, m: int, s: int):
        """타이머 시간 재설정"""
        self.timer.set_time(h, m, s)

    async def start_game(self):
        """게임 시작"""
        if self.is_active:
            # 이미 진행 중이면 리셋 후 재시작
            print(f"[Group {self.group_name}] Already active, resetting timer.")
            await self.timer.reset()
            await self.timer.start()
            return

        self.is_active = True
        self.now_turn = 0
        await self.timer.reset()
        await self.timer.start()

    async def stop_game(self):
        """게임 정지"""
        if not self.is_active:
            raise ValueError("[Group] Game is not active.")
        self.is_active = False
        self.now_turn = 0
        await self.timer.stop()

    async def pause_game(self):
        await self.timer.pause()

    async def resume_game(self):
        await self.timer.resume()

    async def turn_over(self):
        """턴 전환 로직 (3초 대기 후 다음 턴)"""
        if not self.is_active:
            raise ValueError("[Group] Game is not active.")

        # 타이머 일시 정지
        await self.timer.stop()

        # 3초 대기 + 브로드캐스트
        for i in range(3, 0, -1):
            msg = json.dumps({
                "action": "turn_wait",
                "now_turn": self.now_turn,
                "remaining_wait_seconds": i,
            })
            await self.broadcast_callback(self.group_name, msg)
            await asyncio.sleep(1)

        # 턴 전환
        self.now_turn = (self.now_turn + 1) % len(self.players)
        print(f"[Group {self.group_name}] Turn switched to player {self.now_turn}")

        # 타이머 재설정(예: 30초) 원하는 값으로 설정
        await self.timer.reset()
        print("[group.py] reset() ",self.timer.running)
        # 타이머 재시작
        await self.timer.start()

    def to_dict(self):
        return {
            "group_name": self.group_name,
            "host_player": self.host_player.to_dict(),
            "players": [p.to_dict() for p in self.players],
            "now_turn": self.now_turn,
            "is_active": self.is_active,
            "remaining_time": self.timer.remaining_seconds
        }
