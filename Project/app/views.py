from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count
import json
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from .models import ChatRoom, Message, FriendRequest, Friendship


@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not password:
            return JsonResponse({'error': 'Username and password required'}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)

        user = User.objects.create_user(
            username=username,
            email=email or '',
            password=password
        )

        return JsonResponse({
            'message': 'User created successfully',
            'user_id': user.id,
            'username': user.username
        }, status=201)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        user = authenticate(username=username, password=password)

        if user:
            payload = {
                'user_id': user.id,
                'username': user.username,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }
            token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

            return JsonResponse({
                'token': token,
                'user_id': user.id,
                'username': user.username
            })

        return JsonResponse({'error': 'Invalid credentials'}, status=401)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_user_from_token(request):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user = User.objects.get(id=payload['user_id'])
        return user
    except:
        return None


@require_http_methods(["GET"])
def profile(request):
    user = get_user_from_token(request)
    
    if not user:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    return JsonResponse({
        'id': user.id,
        'username': user.username,
        'email': user.email
    })


@csrf_exempt
@require_http_methods(["POST"])
def send_friend_request(request):
    user = get_user_from_token(request)
    
    if not user:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        data = json.loads(request.body)
        receiver_id = data.get('receiver_id')
        
        if not receiver_id:
            return JsonResponse({'error': 'receiver_id required'}, status=400)

        receiver = User.objects.get(id=receiver_id)

        if user.id == receiver.id:
            return JsonResponse({'error': 'Cannot send friend request to yourself'}, status=400)

        if Friendship.are_friends(user, receiver):
            return JsonResponse({'error': 'Already friends'}, status=400)

        existing_request = FriendRequest.objects.filter(
            Q(sender=user, receiver=receiver) | Q(sender=receiver, receiver=user),
            status='pending'
        ).first()

        if existing_request:
            return JsonResponse({'error': 'Friend request already exists'}, status=400)

        friend_request = FriendRequest.objects.create(
            sender=user,
            receiver=receiver
        )

        return JsonResponse({
            'message': 'Friend request sent',
            'request_id': friend_request.id
        }, status=201)

    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def respond_friend_request(request, request_id):
    user = get_user_from_token(request)
    
    if not user:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        data = json.loads(request.body)
        action = data.get('action')  

        if action not in ['accept', 'reject']:
            return JsonResponse({'error': 'Invalid action'}, status=400)

        friend_request = FriendRequest.objects.get(id=request_id, receiver=user, status='pending')

        if action == 'accept':
            friend_request.status = 'accepted'
            friend_request.save()

            Friendship.objects.create(
                user1=friend_request.sender,
                user2=friend_request.receiver
            )

            ChatRoom.get_private_chat(friend_request.sender, friend_request.receiver)

            return JsonResponse({'message': 'Friend request accepted'})
        else:
            friend_request.status = 'rejected'
            friend_request.save()
            return JsonResponse({'message': 'Friend request rejected'})

    except FriendRequest.DoesNotExist:
        return JsonResponse({'error': 'Friend request not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_friend_requests(request):
    user = get_user_from_token(request)
    
    if not user:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    received = FriendRequest.objects.filter(receiver=user, status='pending')
    sent = FriendRequest.objects.filter(sender=user, status='pending')

    received_data = [{
        'id': req.id,
        'sender_id': req.sender.id,
        'sender_username': req.sender.username,
        'created_at': req.created_at.isoformat()
    } for req in received]

    sent_data = [{
        'id': req.id,
        'receiver_id': req.receiver.id,
        'receiver_username': req.receiver.username,
        'created_at': req.created_at.isoformat()
    } for req in sent]

    return JsonResponse({
        'received': received_data,
        'sent': sent_data
    })


@require_http_methods(["GET"])
def get_friends(request):
    user = get_user_from_token(request)
    
    if not user:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    friends = Friendship.get_friends(user)

    friends_data = [{
        'id': friend.id,
        'username': friend.username,
        'email': friend.email
    } for friend in friends]

    return JsonResponse({'friends': friends_data})


@require_http_methods(["GET"])
def search_users(request):
    user = get_user_from_token(request)
    
    if not user:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    query = request.GET.get('q', '').strip()

    if not query:
        return JsonResponse({'users': []})

    users = User.objects.filter(
        Q(username__icontains=query) | Q(email__icontains=query)
    ).exclude(id=user.id)[:20]

    friends = Friendship.get_friends(user)
    friend_ids = [f.id for f in friends]

    sent_request_ids = list(FriendRequest.objects.filter(
        sender=user, status='pending'
    ).values_list('receiver_id', flat=True))

    received_request_ids = list(FriendRequest.objects.filter(
        receiver=user, status='pending'
    ).values_list('sender_id', flat=True))

    users_data = []
    for u in users:
        status = 'none'
        if u.id in friend_ids:
            status = 'friend'
        elif u.id in sent_request_ids:
            status = 'request_sent'
        elif u.id in received_request_ids:
            status = 'request_received'

        users_data.append({
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'friendship_status': status
        })

    return JsonResponse({'users': users_data})


@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
@require_http_methods(["POST"])
def create_chatroom(request):
    try:
        data = json.loads(request.body)
        
        room_type = data.get('room_type', 'private')
        name = data.get('name', '')
        description = data.get('description', '')

        if room_type == 'anonymous':
            if not name:
                name = f"Anonymous Chat {ChatRoom.objects.filter(room_type='anonymous').count() + 1}"
            
            chatroom = ChatRoom.objects.create(
                name=name,
                room_type='anonymous'
            )
            
            return JsonResponse({
                'room_id': chatroom.id,
                'room_type': chatroom.room_type,
                'name': chatroom.name,
                'message': 'Anonymous chat room created successfully'
            }, status=201)

        user = get_user_from_token(request)
        if not user:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        if room_type == 'private':
            other_user_id = data.get('other_user_id')
            if not other_user_id:
                return JsonResponse({'error': 'other_user_id required for private chat'}, status=400)
            
            other_user = User.objects.get(id=other_user_id)

            if not Friendship.are_friends(user, other_user):
                return JsonResponse({'error': 'You must be friends to chat'}, status=403)

            chatroom = ChatRoom.get_private_chat(user, other_user)
            
            if not chatroom:
                return JsonResponse({'error': 'Failed to create private chat'}, status=500)
            
            return JsonResponse({
                'room_id': chatroom.id,
                'room_type': chatroom.room_type,
                'name': chatroom.name or f"Chat with {other_user.username}"
            }, status=201)
            
        elif room_type == 'group':
            participant_ids = data.get('participant_ids', [])
            
            if not name:
                return JsonResponse({'error': 'Group name required'}, status=400)
            
            if not participant_ids:
                return JsonResponse({'error': 'At least one participant required'}, status=400)
            
            chatroom = ChatRoom.objects.create(
                name=name,
                room_type='group'
            )
            
            chatroom.participants.add(user)
            
            for participant_id in participant_ids:
                try:
                    participant = User.objects.get(id=participant_id)
                    if Friendship.are_friends(user, participant):
                        chatroom.participants.add(participant)
                except User.DoesNotExist:
                    continue
            
            participant_names = [p.username for p in chatroom.participants.all()]
            
            return JsonResponse({
                'room_id': chatroom.id,
                'room_type': chatroom.room_type,
                'name': chatroom.name,
                'participants': participant_names,
                'participant_count': chatroom.participants.count()
            }, status=201)
        else:
            return JsonResponse({'error': 'Invalid room type'}, status=400)

    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@require_http_methods(["GET"])
def get_messages(request, room_id):
    try:
        chatroom = ChatRoom.objects.get(id=room_id)
        
        user = None
        if chatroom.room_type != 'anonymous':
            user = get_user_from_token(request)
            if not user or user not in chatroom.participants.all():
                return JsonResponse({'error': 'Access denied'}, status=403)

        messages = Message.objects.filter(chat_room=chatroom).order_by('timestamp')
        
        messages_data = []
        for msg in messages:
            can_delete = False
            if user:
                can_delete = (msg.sender and msg.sender.id == user.id)
            
            messages_data.append({
                'id': msg.id,
                'content': msg.content,
                'sender_name': msg.anonymous_name or (msg.sender.username if msg.sender else 'Unknown'),
                'sender_id': msg.sender.id if msg.sender else None,
                'anonymous_name': msg.anonymous_name,
                'is_anonymous': bool(msg.anonymous_name),
                'timestamp': msg.timestamp.isoformat(),
                'can_delete': can_delete
            })

        return JsonResponse({'messages': messages_data})

    except ChatRoom.DoesNotExist:
        return JsonResponse({'error': 'Chat room not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_chatrooms(request):
    user = get_user_from_token(request)
    
    if not user:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    chatrooms = ChatRoom.objects.filter(participants=user, is_active=True)
    
    rooms_data = []
    for room in chatrooms:
        participants = room.participants.all()
        participant_names = [p.username for p in participants]
        
        display_name = room.name
        if room.room_type == 'private' and not display_name:
            other_users = [p.username for p in participants if p.id != user.id]
            display_name = other_users[0] if other_users else 'Private Chat'
        elif room.room_type == 'group' and not display_name:
            display_name = f"Group Chat ({participants.count()} members)"
        
        rooms_data.append({
            'id': room.id,
            'name': display_name,
            'room_type': room.room_type,
            'participant_count': participants.count(),
            'participants': participant_names,
            'created_at': room.created_at.isoformat()
        })

    return JsonResponse({'chatrooms': rooms_data})


@require_http_methods(["GET"])
def get_anonymous_rooms(request):
    """List all active anonymous chat rooms with real participant counts"""
    try:
        rooms = ChatRoom.objects.filter(
            room_type='anonymous',
            is_active=True
        ).order_by('-created_at')
        
        rooms_data = []
        for room in rooms:
            one_hour_ago = datetime.now() - timedelta(hours=1)
            recent_messages = Message.objects.filter(
                chat_room=room,
                timestamp__gte=one_hour_ago
            )
            
            anonymous_participants = set(
                msg.anonymous_name for msg in recent_messages 
                if msg.anonymous_name
            )
            auth_participants = set(
                msg.sender_id for msg in recent_messages 
                if msg.sender_id
            )
            
            participant_count = len(anonymous_participants) + len(auth_participants)
            total_messages = Message.objects.filter(chat_room=room).count()
            
            rooms_data.append({
                'id': room.id,
                'name': room.name or f"Room {room.id}",
                'description': '',  # Add description field to model if needed
                'participant_count': participant_count,
                'message_count': total_messages,
                'is_active': participant_count > 0,  # Active if someone messaged recently
                'created_at': room.created_at.isoformat()
            })
        
        rooms_data.sort(key=lambda x: (x['participant_count'], x['created_at']), reverse=True)
        
        return JsonResponse({'rooms': rooms_data})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def join_anonymous_room(request, room_id):
    """Join an anonymous chat room - no auth required"""
    try:
        chatroom = ChatRoom.objects.get(id=room_id, room_type='anonymous')
        
        return JsonResponse({
            'message': 'Joined anonymous chat room',
            'room_id': chatroom.id,
            'room_name': chatroom.name,
            'room_type': 'anonymous'
        })
    
    except ChatRoom.DoesNotExist:
        return JsonResponse({'error': 'Anonymous chat room not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def join_chatroom(request, room_id):
    """Allow users to join existing chat rooms (for groups)"""
    try:
        user = get_user_from_token(request)
        
        if not user:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        chatroom = ChatRoom.objects.get(id=room_id)
        
        if user not in chatroom.participants.all():
            chatroom.participants.add(user)
        
        return JsonResponse({
            'message': 'Joined chat room successfully',
            'room_id': chatroom.id,
            'room_name': chatroom.name
        })
    
    except ChatRoom.DoesNotExist:
        return JsonResponse({'error': 'Chat room not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE", "POST"])
def delete_message(request, message_id):
    """Delete a message - only sender can delete their own messages"""
    try:
        message = Message.objects.get(id=message_id)
        
        if message.anonymous_name:
            return JsonResponse({'error': 'Cannot delete anonymous messages'}, status=403)
        
        user = get_user_from_token(request)
        if not user:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        if message.sender != user:
            return JsonResponse({'error': 'You can only delete your own messages'}, status=403)
        
        chat_room_id = message.chat_room.id
        
        message.delete()
        
        return JsonResponse({
            'message': 'Message deleted successfully',
            'message_id': message_id,
            'chat_room_id': chat_room_id
        })
    
    except Message.DoesNotExist:
        return JsonResponse({'error': 'Message not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
@require_http_methods(["POST"])
def leave_chatroom(request, room_id):
    try:
        user = get_user_from_token(request)
        if not user:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        chatroom = ChatRoom.objects.get(id=room_id)
        
        if user not in chatroom.participants.all():
            return JsonResponse({'error': 'You are not in this chat room'}, status=400)
        
        if chatroom.room_type == 'private':
            return JsonResponse({'error': 'Cannot leave private chats'}, status=400)
        
        chatroom.participants.remove(user)
        
        return JsonResponse({'message': 'Left chat room successfully'})
    
    except ChatRoom.DoesNotExist:
        return JsonResponse({'error': 'Chat room not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)