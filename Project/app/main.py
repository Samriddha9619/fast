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
        try: #exclude user id is made because when a user sends a message the message gets his own message too so in order to prevent it this is made
            chatroom= Chatroom.objects.get(id=chat_room_id)
            participants= chatroom.participants.all()
            sent_count=0
            for user in participants:
                if exclude_user_id and user.id==exclude_user_id:
                    continue
                if await self.send_to_user(user.id,message):
                    sent_count+=1

            print(f"Broadcasted to {sent_count} users in room {chat_room_id}")
            return sent_count
        
        except ChatRoom.DoesNotExist:
            print(f'Chat room {chat_room_id} not found')
            return 0
manager = ConnenctionManager()

async def send_error(websocket:WebSocket,error_message:str):
    await websocket.send_text(json.dumps(
        {
            "type":"error",
            "message":error_message
        }
    ))

async def handle_send_message(websocket:WebSocket,user_id:int,data:dict):
    chat_room_id = data.get('chat_room_id')
    content =data.get('content','').strip()

    if not chat_room_id or not content:
        await send_error(websocket,"Missing chat_room_id or content")
        return
    
    try:
        chatroom = ChatRoom.objects.get(id=chat_room_id)
        user=User.objects.get(id=user_id)

        if user not in chatroom.participants.all():
            await send_error(websocket,"You're not a participant")
            return
        
        message= Message.objects.create(
            content=content,
            sender=user,
            chat_room=chatroom
        )

        broadcast_data={
            "type": "new_message",
            "message_id": message.id,
            "chat_room_id": chat_room_id,
            "content": content,
            "sender_id": user_id,
            "sender_username": user.username,
            "timestamp": message.timestamp.isoformat()
        }

        await manager.broadcast_to_room(chat_room_id,broadcast_data)
        print(f'Message saved and broadcasted: {user.username}-> Room{chat_room_id}')
    
    except ChatRoom.DoesNotExist:
        await send_error(websocket, "Chat room not found")
    except User.DoesNotExist:
        await send_error(websocket, "User not found")
    except Exception as e:
        print(f"Error handling message: {e}")
        await send_error(websocket, "Failed to send message")

async def handle_typing_indicator(websocket:WebSocket,user_id:int,data:dict):
    chat_room_id = data.get('chat_room_id')
    is_typing = data.get('is_typing', False)

    if not chat_room_id:
        await send_error(websocket,"Missing chat_room_id")
        return
    
    try:
        chatroom = ChatRoom.objects.get(id=chat_room_id)
        user = User.objects.get(id=user_id)

        if user not in chatroom.participants.all():
            return # just ignore u don't have to return any error in this scenario
        
        typing_data={
            "type":"user_typing",
            "chat_room_id": chat_room_id,
            "user_id": user_id,
            "username": user.username,
            "is_typing": is_typing
        }

        await manager.broadcast_to_room(chat_room_id,typing_data,exclude_user_id=user_id)
    
    except (ChatRoom.DoesNotExist,User.DoesNotExist):
        pass # just ignore same as above

async def handle_join_room_notification(websocket:WebSocket,user_id:int,data:dict):
    # to notify people already present in the room that the user has joined
    chat_room_id = data.get('chat_room_id')

    if not chat_room_id:
        return
    try:
        chatroom =ChatRoom.objects.get(id=chat_room_id)
        user=User.objects.get(id=user_id)
        if user not in chatroom.participants.all():
            return
    
        join_data=  {
            "type": "user_joined",
            "chat_room_id": chat_room_id,
            "user_id":user_id,
            "username":user.username
            }
        await manager.broadcast_to_room(chat_room_id,join_data,exclude_user_id=user_id)
    except (ChatRoom.DoesNotExist,User.DoesNotExist):
        pass
    
async def handle_message(websocket:WebSocket,user_id:int,raw_data:str):
    try:
        data= json.loads(raw_data)
        message_type=data.get('type')
        if message_type=='send_message':
            await handle_send_message(websocket,user_id,data)
            
        if message_type=='typing':
            await handle_typing_indicator(websocket,user_id,data)
        if message_type=='join_room':
            await handle_join_room_notification(websocket,user_id,data)
        else:
            await send_error(websocket,f"Unknown message type: {message_type}")
    except json.JSONDecodeError:
        await send_error(websocket,"Invalid Json format")
    except Exception as e: 
        print(f'Error handling message: {e}')
        await send_error(websocket,"Internal server error")
@aoo.websocket("/ws")
async def websocket_endpoint(websocket:WebSocket,token:str=Query(...)):
    user_id = validate_token(token)
    if not user_id:
        await websocket.close(code=4001,reason ="Invalid token")
        return
    
    await manager.connect(websocket,user_id)
    try:
        while True:
            raw_data = await websocket.receive.text()
            await handle_message(websocket,user_id,raw_data)
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        print(f"User {user_id} disconencted normally")
    except Exception as e:
        print(f'Websocket error for user {user_id}: {e}')
        manager.disconnect(user_id)
        

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app,host="0.0.0.0",port=8001)