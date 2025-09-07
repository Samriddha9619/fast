import os # without OS Fastapi can't find djnago models and database
import django
import json
from fastapi import FastAPI,WebSocket,WebSocketDisconnect, Query
from typing import Dict

os.environ.setdefault('DJANGO_SETTINGS_MODULE','chatapp.settings')
django.setup()

from django.contrib.auth.models import User
from app.models import ChatRoom, Message
from .auth import validate_token

app = FastAPI()

class ConnenctionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket]

    async def connect(self,websocket:WebSocket,user_id:int):
        await websocket.accept()
        self.active_connections[user_id]= websocket
        print(f"User {user_id} connected. Active connections: {len(self.active_connections)}")

    def disconnect(self,user_id:int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"User {user_id} connected. Active connetions:{len(self.active_connections)}")

    async def send_to_user(self,user_id:int, message:dict):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
                
                '''
json.dumps() is a Python function that converts a Python object into a JSON-formatted string
WebSockets only send text or binary, not Python objects. So you need to serialize your data — turn it into a format that can travel across the wire. JSON is perfect for that because:

It’s lightweight

It’s readable

It’s supported by every frontend framework
                '''
                return True
            except:
                self.disconnect(user_id)#case when the connection broke so disconnect user
                return False
        return False
    
    async def broadcast_to_room(self, chat_room_id:int,message:dict,exclude_user_id:int=None):# can use | for optional
        

    
