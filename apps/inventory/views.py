
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny

from .models import Stock, StockMovement
from .serializers import (
    StockSerializer,
    StockMovementSerializer
)


class StockViewSet(ModelViewSet):

    queryset = Stock.objects.all()

    serializer_class = StockSerializer

    permission_classes = [
        AllowAny
    ]


class StockMovementViewSet(ModelViewSet):

    queryset = StockMovement.objects.all()

    serializer_class = StockMovementSerializer

    permission_classes = [
        AllowAny
    ]