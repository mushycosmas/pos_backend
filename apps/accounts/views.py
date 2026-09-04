from django.contrib.auth import authenticate

from rest_framework import status
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
)


# ============================================================
# USER VIEWSET
# ============================================================

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


# ============================================================
# LOGIN
# ============================================================

class LoginView(APIView):
    permission_classes = [
        AllowAny
    ]

    def post(self, request):

        username = request.data.get('username')
        password = request.data.get('password')

        # ----------------------------------------------------
        # Validate credentials input
        # ----------------------------------------------------

        if not username or not password:
            return Response(
                {
                    'detail': 'Username and password are required.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ----------------------------------------------------
        # Authenticate user
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Check account status
        # ----------------------------------------------------

        if not user.is_active:
            return Response(
                {
                    'detail': 'User account is inactive.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # ----------------------------------------------------
        # Record login IP
        # ----------------------------------------------------

        user.last_login_ip = request.META.get(
            'REMOTE_ADDR'
        )

        user.save(
            update_fields=[
                'last_login_ip'
            ]
        )

        # ----------------------------------------------------
        # Generate JWT tokens
        # ----------------------------------------------------

        refresh = RefreshToken.for_user(user)

        access_token = refresh.access_token

        # ----------------------------------------------------
        # Return authentication response
        # ----------------------------------------------------

        return Response(
            {
                'access': str(access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# CURRENT AUTHENTICATED USER
# ============================================================

class MeView(APIView):
    """
    Return the currently authenticated user.

    Endpoint:
        GET /api/v1/auth/me/

    Requires:
        Valid JWT access token
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        user = request.user

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_200_OK
        )