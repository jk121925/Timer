# your_project/core/player.py

import uuid
from fastapi import WebSocket

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

    def __eq__(self, player_name):
        if player_name is None:
            return False
        return self.player_name == player_name
