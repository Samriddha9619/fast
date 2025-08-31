from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
import json 

from django.http import JsonResponse
from .models import ChatRoom, Message


@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    data = json.loads(request.body)
    username = data.get('username')
    password = data.get('password')
    email = data.get('email','')

    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': 'Username already exists'}, status=400)
    user = User.objects.create_user(username=username, password=password, email=email)
    return JsonResponse({'message': 'User registered successfully'}, status=201)

@csrf_exempt
@require_http_methods(["POST"])
def login_user(request):
    data = json.loads(request.body)
    username = data.get('username')
    password = data.get('password')

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return JsonResponse({'message': 'Login successful'}, status=200)
    else:
        return JsonResponse({'error': 'Invalid credentials'}, status=400)
    
@csrf_exempt
@require_http_methods(["POST"])
def logout_user(request):
    logout(request)
    return JsonResponse({'message': 'Logout successful'}, status=200)

@login_required
@require_http_methods(["GET"])
def current_user(request):
    user = request.user
    return JsonResponse({'id':user.id, 'username': user.username, 'email': user.email}, status=200)
def chatrooms_list(request):
    if request.method == "GET":
        rooms=ChatRoom.objects.all()
        rooms.data=[]
        for room in rooms:
            rooms.data.append({
                id:room_id,
                name:room.name,
                created_at:room.created_at.isoformat(),
                participants:[user.username for user in room.participants.all()]#maybe a bug so see it later 
            })
        return JsonResponse(rooms.data, safe=False)
    elif request.method == "POST":
        data = json.loads(request.body)
        room = ChatRoom.objects.create(name=data["name"])
        room.participants.add(request.user)  
        return JsonResponse({
            'id': room.id,
            'name': room.name,
            'created_at': room.created_at.isoformat(),
        })

@csrf_exempt
@login_required

def join_chatroom(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    room.participants.add(request.user)
    return JsonResponse({'message': f'Joined chat room {room.name}'}, status=200)

@login_required

def chatroom_messages(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    messages =Message.objects.filter(chat_room=room).order_by('timestamp')
    messages_data =[]
    for message in messages:
        messages_data.append({
            'id': message.id,
            'content': message.content,
            'sender': message.sender.username,
            'timestamp': message.timestamp.isoformat(),
        })
    return JsonResponse(messages_data, safe=False)

