from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import PaymentMethod
from .serializers import PaymentMethodSerializer


class PaymentMethodViewSet(ModelViewSet):
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PaymentMethod.objects.all()

        is_active = self.request.query_params.get("is_active")
        payment_type = self.request.query_params.get("payment_type")

        if is_active is not None:
            queryset = queryset.filter(
                is_active=is_active.lower() in ["true", "1", "yes"]
            )

        if payment_type:
            queryset = queryset.filter(
                payment_type=payment_type
            )

        return queryset

    @action(
        detail=False,
        methods=["get"],
        url_path="active",
    )
    def active(self, request):
        queryset = self.get_queryset().filter(
            is_active=True
        )

        serializer = self.get_serializer(
            queryset,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="activate",
    )
    def activate(self, request, pk=None):
        payment_method = self.get_object()

        payment_method.is_active = True
        payment_method.save(
            update_fields=["is_active", "updated_at"]
        )

        return Response(
            self.get_serializer(payment_method).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="deactivate",
    )
    def deactivate(self, request, pk=None):
        payment_method = self.get_object()

        payment_method.is_active = False
        payment_method.save(
            update_fields=["is_active", "updated_at"]
        )

        return Response(
            self.get_serializer(payment_method).data,
            status=status.HTTP_200_OK,
        )