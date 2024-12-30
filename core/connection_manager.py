# core/connection_manager.py
from typing import Dict, List, Optional
from fastapi import WebSocket, HTTPException
from models import ClientInfo
import uuid
import asyncio

class Client:
    def __init__(self, websocket: Optional[WebSocket], client_name: str):
        self.websocket = websocket
        self.client_id = str(uuid.uuid4())
        self.client_name = client_name
        self.is_host = False

    def to_dict(self) -> dict:
        return {
            "client_id": self.client_id,
            "client_name": self.client_name
        }

class PlayClient:
    def __init__(self, clients : List[Client],turn: int):
        self.clients = clients
        self.turn = turn
    
    def turn_over(self):
        self.turn +=1
        if self.turn == len(self.clients):
            self.turn =0

    def to_dict(self) -> dict:
        return{
            # "clients" : [client.to_dict() for client in self.clients],
            # "turn" : self.turn,
            "turn_client" : [client.to_dict() for client in self.clients][self.turn]
        }

class ConnectionManager:
    def __init__(self):
        self.groups: Dict[str, List[Client]] = {}
        self.play_groups: Dict[str,List[Client]] = {}
        self.lock = asyncio.Lock()

    async def create_group(self, group_name: Optional[str], websocket: WebSocket, client_name: str):
        async with self.lock:
            if group_name:
                if group_name in self.groups:
                    raise HTTPException(status_code=400, detail="그룹 이름이 이미 존재합니다.")
                final_group_name = f"{group_name}-{uuid.uuid4()}"
            else:
                # Generate a unique group name
                final_group_name = f"group-{uuid.uuid4()}"
                while final_group_name in self.groups:
                    final_group_name = f"group-{uuid.uuid4()}"

            # Create the client and add to the group
            client = Client(websocket, client_name)
            client.is_host = True
            self.groups[final_group_name] = [client]
            print(f"그룹 '{final_group_name}' 생성됨, 클라이언트 '{client.client_id}' 추가됨.")
            return final_group_name, client

    async def join_group(self, group_name: str, websocket: WebSocket, client_name: str):
        async with self.lock:
            if group_name not in self.groups:
                raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")

            # Create the client and add to the group
            client = Client(websocket, client_name)
            self.groups[group_name].append(client)
            print(f"클라이언트 '{client.client_id}'가 그룹 '{group_name}'에 추가됨.")
            return group_name, client

    async def reorder_group(self, group_name: str, new_order: List[str]) -> None:
        """Reorder the clients in the group based on the given order of client IDs."""
        async with self.lock:
            if group_name not in self.groups:
                raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
            
            current_clients = self.groups[group_name]
            client_dict = {client.client_id: client for client in current_clients}

            # 요청된 순서대로 클라이언트 정렬
            reordered_clients = []
            for client_id in new_order:
                if client_id in client_dict:
                    reordered_clients.append(client_dict[client_id])
                else:
                    raise HTTPException(status_code=400, detail=f"잘못된 클라이언트 ID: {client_id}")

            self.groups[group_name] = reordered_clients
            print(f"그룹 '{group_name}'의 순서가 업데이트되었습니다: {[c.client_name for c in reordered_clients]}")

    async def remove_connection_from_group(self, websocket: WebSocket) -> Optional[str]:
        async with self.lock:
            for group_name, clients in list(self.groups.items()):
                for client in clients:
                    if client.websocket == websocket:
                        clients.remove(client)
                        print(f"클라이언트 '{client.client_id}'가 그룹 '{group_name}'에서 제거됨.")
                        # Optionally, remove the group if empty
                        if not clients:
                            del self.groups[group_name]
                            print(f"그룹 '{group_name}'가 비워져 삭제됨.")
                        return group_name
            return None

    async def start_game(self, group_name:str):
        async with self.lock:
            if group_name in self.groups:
                starting_group = self.groups.pop(group_name)
                self.play_groups[group_name] = PlayClient(starting_group,0)
            return group_name
    
    async def stop_game(self, group_name:str):
        async with self.lock:
            if group_name in self.play_groups:
                pause_group = self.play_groups.pop(group_name)
                self.groups[group_name] = pause_group.clients
            return group_name

    async def broadcast_to_group(self, group_name: str, message: str):
        async with self.lock:
            if group_name in self.groups:
                for client in self.groups[group_name]:
                    if client.websocket:
                        try:
                            await client.websocket.send_text(message)
                        except Exception as e:
                            print(f"메시지 전송 실패: {e}")

    def get_clients_in_group(self, group_name: str) -> List[ClientInfo]:
        if group_name in self.groups:
            return [ClientInfo(**client.to_dict()) for client in self.groups[group_name]]
        else:
            return []

# 싱글턴 패턴으로 인스턴스 생성
manager = ConnectionManager()
