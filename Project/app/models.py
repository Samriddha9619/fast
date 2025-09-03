from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete= models.CASCADE,related_name="profile")
    avatar = models.URLField(blank=True,null=True)
    bio= models.TextField(blank=True,null=True)
    is_online= models.BooleanField(default=False)
    last_seen= models.DateTimeField(blank=True,null=True)

    def __str__(self):
        return self.user.username

class ChatRoom(models.Model):
    ROOM_TYPES=(
        ('private','Private'),
        ('group','Group'),
    )
    name = models.CharField(max_length=255)
    room_type=models.CharField(max_length=10,choices=ROOM_TYPES,default='private')
    created_at = models.DateTimeField(auto_now_add=True)
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    is_active=models.BooleanField(default=True)


    def __str__(self):
        if self.room_type == 'private':
            return f"Private Chat between {', '.join([user.username for user in self.participants.all()])}"
        return self.name or "Unnamed Group"
    @classmethod
    def get_private_chat(cls,user1,user2):
        chats=cls.objects.filter(room_type="private",participants=user1).filter(participants=user2)
        if chats.exists():
            return chats.first()
        chat= cls.objects.create(room_type="private")
        chat.participants.add(user1,user2)
        return chat

class FriendRequest(models.Model):
    Status_Choices=(
        ("pending","Pending"),
        ("accepter","Accepter"),
        ("rejected","Rejected"),
    )
    sender=models.ForeignKey(User,on_delete=models.CASCADE,related_name="sent_requests")
    receiver=models.ForeignKey(User,on_delete=models.CASCADE,related_name="recieved_requests")
    status=models.CharField(max_length=10,choices=Status_Choices,default="pending")
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["sender", "receiver"],
                condition=Q(status="pending"),
                name="unique_pending_request"
            )
        ]
    def __str__(self):
        return f"{self.sender.username}-> {self.receiver.username} ({self.status})"

class Message(models.Model):
    content = models.TextField()
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"
    
