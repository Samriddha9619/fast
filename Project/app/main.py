from typing import Dict,Set, Annotated
from datetime import datetime
from fastapi import WebSocket,WebSocketDisconnect, FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import sqlite3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:3000","http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections:Dict[int,Set[WebSocket]]={}

    async def connect(self,websocket:WebSocket,room_id:int):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id]=set()
        self.active_connections[room_id].add(websocket)
    
    def disconnect(self,websocket:WebSocket,room_id:int):
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
            
    async def broadcast_to_room(self,message:str,room_id:int):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id].copy():
                try:
                    await connection.send_text(message)
                except:
                    self.active_connections[room_id].discard(connection)


manager= ConnectionManager()

def get_db_connection():
    return sqlite3.connect('db.sqlite3')

def save_message_to_db(content:str,room_id:int,sender_id:int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_message (content, sender_id, chat_room_id, timestamp)
        VALUES (?, ?, ?, ?)
    """, (content, sender_id, room_id, datetime.now()))
    
    message_id = cursor.lastrowid
    
    # Get sender username
    cursor.execute("SELECT username FROM auth_user WHERE id = ?", (sender_id,))
    sender_result = cursor.fetchone()
    sender_username = sender_result[0] if sender_result else "Unknown"
    
    conn.commit()
    conn.close()
    
    return {
        'id': message_id,
        'content': content,
        'sender': {'id': sender_id, 'username': sender_username},
        'timestamp': datetime.now().isoformat()
    }

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket:WebSocket,room_id:int):
    await manager.connect(websocket,room_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            saved_message = save_message_to_db(
                message_data['content'],
                message_data['sender_id'],
                room_id
            )

            broadcast_data ={
                'type': 'message',
                'data': saved_message

            }
            await manager.broadcast_to_room(json.dumps(broadcast_data),room_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket,room_id)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/rooms/{room_id}/online")
async def get_online_users(room_id:int):
    connection_count = len(manager.active_connections.get(room_id, set()))
    return {"online_users": connection_count}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)