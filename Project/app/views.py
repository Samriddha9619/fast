from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import(
    UserLoginSerializer,
    UserProfile,
    UserRegistrationSerializer
)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class=UserRegistrationSerializer

class LoginView(generics.GenericAPIView):
    serializer_class= UserLoginSerializer

    def post(self,request):
        serializer= self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            })
        return Response({"error":"Invalid credentials"},status=status.HTTP_401_UNAUTHORIZED)
    
class ProfileView(generics.RetrieveAPIView):
    serializer_class=UserProfile
    permission_classes= [IsAuthenticated]

    def get_object(self):
        return self.request.user