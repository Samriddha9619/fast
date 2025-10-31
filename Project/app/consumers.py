import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import ChatRoom, Message
import jwt
from django.conf import settings

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope['query_string'].decode()
        self.token = None
        self.anonymous = False
        self.anonymous_name = "Anonymous"
        
        if 'token=' in query_string:
            self.token = query_string.split('token=')[-1].split('&')[0]
        if 'anonymous=true' in query_string:
            self.anonymous = True
        if 'anonymous_name=' in query_string:
            name_part = query_string.split('anonymous_name=')[-1].split('&')[0]
            self.anonymous_name = name_part.replace('%20', ' ')
        
        self.user = await self.get_user_from_token(self.token) if not self.anonymous else None
        self.room_groups = set()
        
        await self.accept()
        
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to WebSocket',
            'is_anonymous': self.anonymous
        }))

    async def disconnect(self, close_code):
        for room_group_name in self.room_groups:
            await self.channel_layer.group_discard(
                room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'join_room':
                await self.join_room(data)
            elif message_type == 'send_message':
                await self.send_chat_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'delete_message':
                await self.delete_chat_message(data)

        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def join_room(self, data):
        room_id = data.get('chat_room_id')
        
        if not room_id:
            return

        room_group_name = f'chat_{room_id}'
        
        await self.channel_layer.group_add(
            room_group_name,
            self.channel_name
        )
        
        self.room_groups.add(room_group_name)
        
        room_info = await self.get_room_info(room_id)
        
        if room_info and room_info['room_type'] == 'anonymous':
            await self.channel_layer.group_send(
                room_group_name,
                {
                    'type': 'user_joined',
                    'user_name': self.anonymous_name,
                    'chat_room_id': room_id,
                    'is_anonymous': True
                }
            )

    async def send_chat_message(self, data):
        room_id = data.get('chat_room_id')
        content = data.get('content', '').strip()
        anonymous_name = data.get('anonymous_name', self.anonymous_name)
        
        if not room_id or not content:
            return

        message_data = await self.save_message(room_id, content, anonymous_name)
        
        if not message_data:
            return

        room_group_name = f'chat_{room_id}'
        
        await self.channel_layer.group_send(
            room_group_name,
            {
                'type': 'new_message',
                'message': message_data
            }
        )

    async def handle_typing(self, data):
        room_id = data.get('chat_room_id')
        is_typing = data.get('is_typing', False)
        
        if not room_id:
            return

        room_group_name = f'chat_{room_id}'
        user_name = self.anonymous_name if self.anonymous else (self.user.username if self.user else 'Someone')
        
        await self.channel_layer.group_send(
            room_group_name,
            {
                'type': 'user_typing',
                'user_name': user_name,
                'is_typing': is_typing,
                'chat_room_id': room_id,
                'sender_channel': self.channel_name
            }
        )

    async def new_message(self, event):
        message = event['message']
        
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'id': message['id'],
            'chat_room_id': message['chat_room_id'],
            'content': message['content'],
            'sender_id': message['sender_id'],
            'sender_name': message['sender_name'],
            'anonymous_name': message.get('anonymous_name', ''),
            'timestamp': message['timestamp']
        }))

    async def user_typing(self, event):
        if event.get('sender_channel') != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'user_typing',
                'user_name': event['user_name'],
                'is_typing': event['is_typing'],
                'chat_room_id': event['chat_room_id']
            }))

    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_name': event['user_name'],
            'chat_room_id': event['chat_room_id'],
            'is_anonymous': event.get('is_anonymous', False)
        }))

    @database_sync_to_async
    def get_user_from_token(self, token):
        if not token:
            return None
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])
            return user
        except:
            return None

    @database_sync_to_async
    def get_room_info(self, room_id):
        try:
            room = ChatRoom.objects.get(id=room_id)
            return {
                'id': room.id,
                'name': room.name,
                'room_type': room.room_type
            }
        except ChatRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def save_message(self, room_id, content, anonymous_name=''):
        try:
            room = ChatRoom.objects.get(id=room_id)
            
            if room.room_type == 'anonymous' or anonymous_name:
                message = Message.objects.create(
                    chat_room=room,
                    content=content,
                    anonymous_name=anonymous_name,
                    sender=self.user if self.user and not self.anonymous else None
                )
            else:
                if not self.user:
                    return None
                
                if self.user not in room.participants.all():
                    return None
                
                message = Message.objects.create(
                    chat_room=room,
                    content=content,
                    sender=self.user
                )
            
            return {
                'id': message.id,
                'chat_room_id': room_id,
                'content': message.content,
                'sender_id': message.sender.id if message.sender else None,
                'sender_name': message.sender.username if message.sender else anonymous_name,
                'anonymous_name': message.anonymous_name,
                'timestamp': message.timestamp.isoformat()
            }
        
        except ChatRoom.DoesNotExist:
            return None
        except Exception as e:
            print(f"Error saving message: {e}")
            return None