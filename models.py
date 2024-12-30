# models.py
from pydantic import BaseModel

class ClientInfo(BaseModel):
    client_id: str
    client_name: str

class BroadcastMessage(BaseModel):
    message: str

class ClientAddRequest(BaseModel):
    inviter_client_id: str  # ID of the client who is inviting
    client_name: str        # Name of the new client to be added
