from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta: 
        model= User
        fields= ['username','email','password']

    def create(self,validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )

        UserProfile.objects.create(user=user)
        return user
    
class UserLoginSerializer(serializers.ModelSerializer):
    username=serializers.CharField()
    password=serializers.CharField(write_only=True)

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=['id','username','email']