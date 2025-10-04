from django.contrib import admin
from .models import ChatRoom, Message, FriendRequest, Friendship

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'room_type', 'created_at', 'is_active']
    list_filter = ['room_type', 'is_active']
    filter_horizontal = ['participants']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_sender', 'chat_room', 'content_preview', 'timestamp']
    list_filter = ['chat_room', 'timestamp']
    search_fields = ['content', 'anonymous_name']

    def get_sender(self, obj):
        if obj.anonymous_name:
            return f"Anonymous: {obj.anonymous_name}"
        return obj.sender.username if obj.sender else "Unknown"
    get_sender.short_description = 'Sender'

    def content_preview(self, obj):
        return obj.content[:50]
    content_preview.short_description = 'Content'

@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'receiver', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['sender__username', 'receiver__username']

@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ['id', 'user1', 'user2', 'created_at']
    search_fields = ['user1__username', 'user2__username']