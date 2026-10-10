from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Stock, StockMovement
from .serializers import (
    StockSerializer,
    StockMovementSerializer,
)


def get_requested_branch_id(request):
    value = (
        request.query_params.get("branch")
        or request.query_params.get("branch_id")
    )

    if value in (None, ""):
        return None

    try:
        branch_id = int(value)
    except (TypeError, ValueError):
        return None

    return branch_id if branch_id > 0 else None


class StockViewSet(ModelViewSet):
    serializer_class = StockSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Stock.objects.select_related(
            "product",
            "product__category",
            "branch",
        )

        branch_value = (
            self.request.query_params.get("branch")
            or self.request.query_params.get("branch_id")
        )

        # Require a branch for list requests.
        if self.action == "list":
            branch_id = get_requested_branch_id(self.request)

            if branch_id is None:
                return queryset.none()

            return queryset.filter(branch_id=branch_id)

        # For detail requests, honor branch when supplied.
        if branch_value not in (None, ""):
            branch_id = get_requested_branch_id(self.request)

            if branch_id is None:
                return queryset.none()

            queryset = queryset.filter(branch_id=branch_id)

        return queryset

    @action(
        detail=True,
        methods=["patch"],
        url_path="adjust",
    )
    def adjust_stock(self, request, pk=None):
        stock = self.get_object()

        quantity = request.data.get("quantity")
        movement_type = str(
            request.data.get("type", "")
        ).upper()
        reason = str(
            request.data.get("reason", "")
        ).strip()
        reference = request.data.get("reference", "")
        notes = request.data.get("notes", "")

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return Response(
                {"error": "quantity must be a valid integer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if quantity <= 0:
            return Response(
                {"error": "quantity must be greater than zero"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if movement_type not in ("ADD", "REMOVE"):
            return Response(
                {"error": "type must be ADD or REMOVE"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not reason:
            return Response(
                {"error": "reason is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            stock = Stock.objects.select_for_update().get(
                pk=stock.pk
            )

            previous_quantity = stock.quantity

            if movement_type == "ADD":
                new_quantity = previous_quantity + quantity
                movement_type_db = "IN"
            else:
                if quantity > previous_quantity:
                    return Response(
                        {
                            "error": (
                                "Insufficient stock. "
                                f"Available: {previous_quantity}"
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                new_quantity = previous_quantity - quantity
                movement_type_db = "OUT"

            stock.quantity = new_quantity
            stock.save(update_fields=[
                "quantity",
                "last_updated",
            ])

            movement = StockMovement.objects.create(
                product=stock.product,
                branch=stock.branch,
                quantity=quantity,
                previous_quantity=previous_quantity,
                new_quantity=new_quantity,
                movement_type=movement_type_db,
                reference=reference or "",
                notes=notes or reason,
                created_by=(
                    request.user
                    if request.user.is_authenticated
                    else None
                ),
            )

        return Response(
            {
                "stock": StockSerializer(stock).data,
                "movement": StockMovementSerializer(movement).data,
            },
            status=status.HTTP_200_OK,
        )


class StockMovementViewSet(ModelViewSet):
    serializer_class = StockMovementSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = StockMovement.objects.select_related(
            "product",
            "branch",
            "created_by",
        )

        branch_value = (
            self.request.query_params.get("branch")
            or self.request.query_params.get("branch_id")
        )

        # Movement lists must be scoped to a selected branch.
        if self.action == "list":
            branch_id = get_requested_branch_id(self.request)

            if branch_id is None:
                return queryset.none()

            return queryset.filter(branch_id=branch_id)

        if branch_value not in (None, ""):
            branch_id = get_requested_branch_id(self.request)

            if branch_id is None:
                return queryset.none()

            queryset = queryset.filter(branch_id=branch_id)

        return queryset