from django.urls import path
from . import views

urlpatterns = [
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/profile/', views.profile, name='profile'),
    
    path('friends/', views.get_friends, name='get_friends'),
    path('friends/requests/', views.get_friend_requests, name='get_friend_requests'),
    path('friends/requests/send/', views.send_friend_request, name='send_friend_request'),
    path('friends/requests/<int:request_id>/respond/', views.respond_friend_request, name='respond_friend_request'),
    
    path('users/search/', views.search_users, name='search_users'),
    
    path('chatrooms/', views.get_chatrooms, name='get_chatrooms'),
    path('chatrooms/create/', views.create_chatroom, name='create_chatroom'),
    path('chatrooms/<int:room_id>/messages/', views.get_messages, name='get_messages'),
    path('chatrooms/<int:room_id>/join/', views.join_chatroom, name='join_chatroom'),
    path('chatrooms/<int:room_id>/leave/', views.leave_chatroom, name='leave_chatroom'),
    
    path('chatrooms/anonymous/', views.get_anonymous_rooms, name='get_anonymous_rooms'),
    path('chatrooms/anonymous/<int:room_id>/join/', views.join_anonymous_room, name='join_anonymous_room'),
    
    path('messages/<int:message_id>/', views.delete_message, name='delete_message'),
]