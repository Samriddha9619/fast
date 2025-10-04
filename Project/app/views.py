from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q
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

    # Received requests
    received = FriendRequest.objects.filter(receiver=user, status='pending')
    # Sent requests
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
def create_chatroom(request):
    try:
        user = get_user_from_token(request)
        data = json.loads(request.body)
        
        room_type = data.get('room_type', 'private')
        name = data.get('name', '')

        if room_type == 'anonymous':
            chatroom = ChatRoom.objects.create(
                name=name or 'Anonymous Chat',
                room_type='anonymous'
            )
            return JsonResponse({
                'room_id': chatroom.id,
                'room_type': chatroom.room_type,
                'name': chatroom.name
            }, status=201)

        if not user:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        if room_type == 'private':
            other_user_id = data.get('other_user_id')
            if not other_user_id:
                return JsonResponse({'error': 'other_user_id required for private chat'}, status=400)
            
            other_user = User.objects.get(id=other_user_id)

            # Check if they are friends
            if not Friendship.are_friends(user, other_user):
                return JsonResponse({'error': 'You must be friends to chat'}, status=403)

            chatroom = ChatRoom.get_private_chat(user, other_user)
        else:
            chatroom = ChatRoom.objects.create(
                name=name,
                room_type='group'
            )
            chatroom.participants.add(user)

        return JsonResponse({
            'room_id': chatroom.id,
            'room_type': chatroom.room_type,
            'name': chatroom.name
        }, status=201)

    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_messages(request, room_id):
    try:
        chatroom = ChatRoom.objects.get(id=room_id)
        
        if chatroom.room_type != 'anonymous':
            user = get_user_from_token(request)
            if not user or user not in chatroom.participants.all():
                return JsonResponse({'error': 'Access denied'}, status=403)

        messages = Message.objects.filter(chat_room=chatroom).order_by('timestamp')
        
        messages_data = []
        for msg in messages:
            messages_data.append({
                'id': msg.id,
                'content': msg.content,
                'sender_name': msg.anonymous_name or (msg.sender.username if msg.sender else 'Unknown'),
                'sender_id': msg.sender.id if msg.sender else None,
                'is_anonymous': bool(msg.anonymous_name),
                'timestamp': msg.timestamp.isoformat()
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
        rooms_data.append({
            'id': room.id,
            'name': room.name,
            'room_type': room.room_type,
            'created_at': room.created_at.isoformat()
        })

    return JsonResponse({'chatrooms': rooms_data})