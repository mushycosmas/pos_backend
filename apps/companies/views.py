from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny

from .models import Company
from .serializers import CompanySerializer


class CompanyViewSet(ModelViewSet):

    queryset = Company.objects.all()

    serializer_class = CompanySerializer

    permission_classes = [
        AllowAny
    ]