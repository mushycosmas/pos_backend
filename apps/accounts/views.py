from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny

from .models import User
from .serializers import (
    UserSerializer,
    UserCreateSerializer
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