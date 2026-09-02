from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all().select_related(
        'branch'
    )

    permission_classes = [
        AllowAny
    ]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer

        return UserSerializer


class LoginView(APIView):
    permission_classes = [
        AllowAny
    ]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {
                    'detail': 'Username and password are required.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(
            request=request,
            username=username,
            password=password
        )

        if user is None:
            return Response(
                {
                    'detail': 'Invalid username or password.'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {
                    'detail': 'User account is inactive.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Record login IP
        user.last_login_ip = request.META.get('REMOTE_ADDR')
        user.save(
            update_fields=['last_login_ip']
        )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
            },
            status=status.HTTP_200_OK
        )