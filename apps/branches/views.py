from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny

from .models import Branch
from .serializers import BranchSerializer


class BranchViewSet(ModelViewSet):

    queryset = Branch.objects.all()

    serializer_class = BranchSerializer

    permission_classes = [
        AllowAny
    ]