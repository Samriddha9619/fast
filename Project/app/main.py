import os
import django
import json
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from typing import Dict, Optional

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_app.settings')
django.setup()

from django.contrib.auth.models import User
from app.models import ChatRoom, Message

app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_to_connection: Dict[int, str] = {}

    async def connect(self, websocket: WebSocket, connection_id: str, user_id: Optional[int] = None):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        if user_id:
            self.user_to_connection[user_id] = connection_id
        print(f"Connection {connection_id} established. Active: {len(self.active_connections)}")

    def disconnect(self, connection_id: str, user_id: Optional[int] = None):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if user_id and user_id in self.user_to_connection:
            del self.user_to_connection[user_id]
        print(f"Connection {connection_id} closed. Active: {len(self.active_connections)}")

    async def send_to_connection(self, connection_id: str, message: dict):
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(json.dumps(message))
                return True
            except:
                self.disconnect(connection_id)
                return False
        return False

    async def broadcast_to_room(self, chat_room_id: int, message: dict, exclude_connection_id: str = None):
        try:
            chatroom = ChatRoom.objects.get(id=chat_room_id)
            sent_count = 0

            if chatroom.room_type == 'anonymous':
                for conn_id, ws in list(self.active_connections.items()):
                    if exclude_connection_id and conn_id == exclude_connection_id:
                        continue
                    if await self.send_to_connection(conn_id, message):
                        sent_count += 1
            else:
                participants = chatroom.participants.all()
                for user in participants:
                    if user.id in self.user_to_connection:
                        conn_id = self.user_to_connection[user.id]
                        if exclude_connection_id and conn_id == exclude_connection_id:
                            continue
                        if await self.send_to_connection(conn_id, message):
                            sent_count += 1

            print(f"Broadcasted to {sent_count} connections in room {chat_room_id}")
            return sent_count
        except ChatRoom.DoesNotExist:
            print(f'Chat room {chat_room_id} not found')
            return 0


manager = ConnectionManager()


async def send_error(websocket: WebSocket, error_message: str):
    await websocket.send_text(json.dumps({
        "type": "error",
        "message": error_message
    }))


async def handle_send_message(websocket: WebSocket, connection_id: str, user_id: Optional[int], data: dict):
    chat_room_id = data.get('chat_room_id')
    content = data.get('content', '').strip()
    anonymous_name = data.get('anonymous_name', '').strip()

    if not chat_room_id or not content:
        await send_error(websocket, "Missing chat_room_id or content")
        return

    try:
        chatroom = ChatRoom.objects.get(id=chat_room_id)

        if chatroom.room_type == 'anonymous':
            if not anonymous_name:
                anonymous_name = f"Anonymous_{connection_id[:8]}"
            
            message = Message.objects.create(
                content=content,
                anonymous_name=anonymous_name,
                chat_room=chatroom
            )

            broadcast_data = {
                "type": "new_message",
                "message_id": message.id,
                "chat_room_id": chat_room_id,
                "content": content,
                "sender_name": anonymous_name,
                "is_anonymous": True,
                "timestamp": message.timestamp.isoformat()
            }
        else:
            if not user_id:
                await send_error(websocket, "Authentication required for this room")
                return

            user = User.objects.get(id=user_id)
            
            if user not in chatroom.participants.all():
                await send_error(websocket, "You're not a participant")
                return

            message = Message.objects.create(
                content=content,
                sender=user,
                chat_room=chatroom
            )

            broadcast_data = {
                "type": "new_message",
                "message_id": message.id,
                "chat_room_id": chat_room_id,
                "content": content,
                "sender_id": user_id,
                "sender_name": user.username,
                "is_anonymous": False,
                "timestamp": message.timestamp.isoformat()
            }

        await manager.broadcast_to_room(chat_room_id, broadcast_data)
        print(f'Message saved and broadcasted in room {chat_room_id}')

    except ChatRoom.DoesNotExist:
        await send_error(websocket, "Chat room not found")
    except User.DoesNotExist:
        await send_error(websocket, "User not found")
    except Exception as e:
        print(f"Error handling message: {e}")
        await send_error(websocket, "Failed to send message")


async def handle_typing_indicator(websocket: WebSocket, connection_id: str, user_id: Optional[int], data: dict):
    chat_room_id = data.get('chat_room_id')
    is_typing = data.get('is_typing', False)
    anonymous_name = data.get('anonymous_name', '').strip()

    if not chat_room_id:
        return

    try:
        chatroom = ChatRoom.objects.get(id=chat_room_id)

        if chatroom.room_type == 'anonymous':
            if not anonymous_name:
                anonymous_name = f"Anonymous_{connection_id[:8]}"

            typing_data = {
                "type": "user_typing",
                "chat_room_id": chat_room_id,
                "user_name": anonymous_name,
                "is_typing": is_typing,
                "is_anonymous": True
            }
        else:
            if not user_id:
                return

            user = User.objects.get(id=user_id)
            
            if user not in chatroom.participants.all():
                return

            typing_data = {
                "type": "user_typing",
                "chat_room_id": chat_room_id,
                "user_id": user_id,
                "user_name": user.username,
                "is_typing": is_typing,
                "is_anonymous": False
            }

        await manager.broadcast_to_room(chat_room_id, typing_data, exclude_connection_id=connection_id)

    except (ChatRoom.DoesNotExist, User.DoesNotExist):
        pass


async def handle_join_room(websocket: WebSocket, connection_id: str, user_id: Optional[int], data: dict):
    chat_room_id = data.get('chat_room_id')
    anonymous_name = data.get('anonymous_name', '').strip()

    if not chat_room_id:
        return

    try:
        chatroom = ChatRoom.objects.get(id=chat_room_id)

        if chatroom.room_type == 'anonymous':
            if not anonymous_name:
                anonymous_name = f"Anonymous_{connection_id[:8]}"

            join_data = {
                "type": "user_joined",
                "chat_room_id": chat_room_id,
                "user_name": anonymous_name,
                "is_anonymous": True
            }
        else:
            if not user_id:
                return

            user = User.objects.get(id=user_id)
            
            if user not in chatroom.participants.all():
                return

            join_data = {
                "type": "user_joined",
                "chat_room_id": chat_room_id,
                "user_id": user_id,
                "user_name": user.username,
                "is_anonymous": False
            }

        await manager.broadcast_to_room(chat_room_id, join_data, exclude_connection_id=connection_id)

    except (ChatRoom.DoesNotExist, User.DoesNotExist):
        pass


async def handle_message(websocket: WebSocket, connection_id: str, user_id: Optional[int], raw_data: str):
    try:
        data = json.loads(raw_data)
        message_type = data.get('type')

        if message_type == 'send_message':
            await handle_send_message(websocket, connection_id, user_id, data)
        elif message_type == 'typing':
            await handle_typing_indicator(websocket, connection_id, user_id, data)
        elif message_type == 'join_room':
            await handle_join_room(websocket, connection_id, user_id, data)
        else:
            await send_error(websocket, f"Unknown message type: {message_type}")

    except json.JSONDecodeError:
        await send_error(websocket, "Invalid JSON format")
    except Exception as e:
        print(f'Error handling message: {e}')
        await send_error(websocket, "Internal server error")


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    anonymous: bool = Query(False)
):
    connection_id = str(uuid.uuid4())
    user_id = None

    if not anonymous and token:
        from django.contrib.auth import get_user_model
        import jwt
        from django.conf import settings

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
        except:
            await websocket.close(code=4001, reason="Invalid token")
            return

    await manager.connect(websocket, connection_id, user_id)

    try:
        while True:
            raw_data = await websocket.receive_text()
            await handle_message(websocket, connection_id, user_id, raw_data)
    except WebSocketDisconnect:
        manager.disconnect(connection_id, user_id)
        print(f"Connection {connection_id} disconnected normally")
    except Exception as e:
        print(f'WebSocket error for connection {connection_id}: {e}')
        manager.disconnect(connection_id, user_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)