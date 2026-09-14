from django.shortcuts import render

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

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

    # ==========================================================
    # RECEIVE PURCHASE
    # ==========================================================
    @action(
        detail=True,
        methods=['post'],
        url_path='receive'
    )
    def receive(self, request, pk=None):

        purchase = self.get_object()

        try:
            # Receive the purchase using the model method
            purchase.receive(
                user=request.user
            )

            # Refresh from database
            purchase.refresh_from_db()

            serializer = self.get_serializer(purchase)

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        except Exception as exc:

            return Response(
                {
                    'detail': str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class PurchaseItemViewSet(ModelViewSet):

    queryset = PurchaseItem.objects.select_related(
        'purchase',
        'product'
    )

    serializer_class = PurchaseItemSerializer

    permission_classes = [
        AllowAny
    ]