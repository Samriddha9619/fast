from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("current_user/", views.current_user, name="current_user"),
    path("chatrooms/", views.chatrooms_list, name="chatrooms_list"),
    path("chatrooms/<int:room_id>/messages/", views.chatroom_messages, name="messages_list"),
    path("chatrooms/<int:room_id>/join/",views.join_chatroom, name="chatroom_join"),
]