from django.db import transaction
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Return
from .serializers import ReturnSerializer

from apps.inventory.models import Stock


class ReturnViewSet(
    viewsets.ModelViewSet
):

    serializer_class = ReturnSerializer

    permission_classes = [
        IsAuthenticated
    ]

    queryset = (
        Return.objects
        .select_related(
            "sale",
            "customer",
            "branch",
            "created_by",
            "approved_by",
        )
        .prefetch_related(
            "items",
            "items__product",
        )
    )

    def get_queryset(self):

        queryset = super().get_queryset()

        return_status = (
            self.request
            .query_params
            .get("status")
        )

        sale_id = (
            self.request
            .query_params
            .get("sale")
        )

        customer_id = (
            self.request
            .query_params
            .get("customer")
        )

        search = (
            self.request
            .query_params
            .get("search")
        )

        if return_status:
            queryset = queryset.filter(
                status=return_status
            )

        if sale_id:
            queryset = queryset.filter(
                sale_id=sale_id
            )

        if customer_id:
            queryset = queryset.filter(
                customer_id=customer_id
            )

        if search:
            queryset = queryset.filter(
                return_number__icontains=search
            )

        return queryset

    @transaction.atomic
    def create(
        self,
        request,
        *args,
        **kwargs
    ):

        serializer = self.get_serializer(
            data=request.data,
            context={
                "request": request
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        return_record = serializer.save()

        return Response(
            self.get_serializer(
                return_record
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
    )
    @transaction.atomic
    def approve(
        self,
        request,
        pk=None
    ):

        return_record = self.get_object()

        if (
            return_record.status
            != Return.STATUS_PENDING
        ):
            return Response(
                {
                    "detail": (
                        "Only pending returns "
                        "can be approved."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return_record.status = (
            Return.STATUS_APPROVED
        )

        return_record.approved_by = (
            request.user
        )

        return_record.approved_at = (
            timezone.now()
        )

        return_record.save(
            update_fields=[
                "status",
                "approved_by",
                "approved_at",
            ]
        )

        return Response(
            self.get_serializer(
                return_record
            ).data
        )

    @action(
        detail=True,
        methods=["post"],
    )
    @transaction.atomic
    def complete(
        self,
        request,
        pk=None
    ):

        return_record = self.get_object()

        if (
            return_record.status
            != Return.STATUS_APPROVED
        ):
            return Response(
                {
                    "detail": (
                        "Only approved returns "
                        "can be completed."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Restore inventory
        for item in (
            return_record
            .items
            .select_related("product")
        ):

            stock = (
                Stock.objects
                .select_for_update()
                .filter(
                    product=item.product,
                    branch=return_record.branch,
                )
                .first()
            )

            if not stock:
                return Response(
                    {
                        "detail": (
                            f"Stock record not found "
                            f"for {item.product.name}."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            stock.quantity += item.quantity

            stock.save(
                update_fields=[
                    "quantity"
                ]
            )

        return_record.status = (
            Return.STATUS_COMPLETED
        )

        return_record.completed_at = (
            timezone.now()
        )

        return_record.save(
            update_fields=[
                "status",
                "completed_at",
            ]
        )

        return Response(
            self.get_serializer(
                return_record
            ).data
        )

    @action(
        detail=True,
        methods=["post"],
    )
    def reject(
        self,
        request,
        pk=None
    ):

        return_record = self.get_object()

        if (
            return_record.status
            != Return.STATUS_PENDING
        ):
            return Response(
                {
                    "detail": (
                        "Only pending returns "
                        "can be rejected."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return_record.status = (
            Return.STATUS_REJECTED
        )

        return_record.save(
            update_fields=["status"]
        )

        return Response(
            self.get_serializer(
                return_record
            ).data
        )