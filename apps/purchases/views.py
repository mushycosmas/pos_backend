from django.shortcuts import render

# Create your views here.
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny


from .models import (
    Purchase,
    PurchaseItem
)


from .serializers import (
    PurchaseSerializer,
    PurchaseItemSerializer
)



class PurchaseViewSet(ModelViewSet):

    queryset = Purchase.objects.select_related(
        'supplier',
        'branch',
        'company'
    ).prefetch_related(
        'items'
    )


    serializer_class = PurchaseSerializer


    permission_classes = [
        AllowAny
    ]



class PurchaseItemViewSet(ModelViewSet):

    queryset = PurchaseItem.objects.select_related(
        'purchase',
        'product'
    )


    serializer_class = PurchaseItemSerializer


    permission_classes = [
        AllowAny
    ]