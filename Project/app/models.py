from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):
    dp = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    is_online=models.BooleanField(default=False)
    last_seen=models.DateTimeField(null=True, blank=True)


class Friend(models.Model):
    user = models.ForeignKey(User, related_name='user', on_delete=models.CASCADE)
    friend = models.ForeignKey(User, related_name='friend', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    
    class Meta:
        verbose_name_plural = "Friends"

    def __str__(self):
        return f"{self.user} - {self.friend}"
    
class Message(models.Model):
    MESSAGE_TYPE=[
        ('text','Text'),
        ('image','Image'),
        ('file','File'),
    ]
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    message_type=models.CharField(max_length=10,default="text") 

class FileAttachement(models.Model):
    message = models.ForeignKey(Message, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='message_attachments/')
    file_name=models.CharField(max_length=255)
    file_size=models.IntegerField()