from django.contrib import admin

# Register your models here.
from .models import ChatRoom, Message

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display=['name','created_at']
    filter_horizontal=['participants']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display=['sender','chat_room','content','timestamp']
    list_filter=['chat_room','timestamp']