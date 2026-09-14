from datetime import timedelta

from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Sale, SaleItem

from .serializers import (
    SaleListSerializer,
    SaleDetailSerializer,
    SaleCreateSerializer,
    SaleUpdateSerializer,
    SaleCancelSerializer,
    SaleReceiptSerializer,
    SaleSummarySerializer,
)

# Inventory
from apps.inventory.models import Stock, StockMovement


# =========================================================
# SALE VIEWSET
# =========================================================

class SaleViewSet(viewsets.ModelViewSet):

    # =====================================================
    # PERMISSIONS
    # =====================================================

    permission_classes = [IsAuthenticated]

    # =====================================================
    # BASE QUERYSET
    # =====================================================

    queryset = (
        Sale.objects
        .select_related(
            "branch",
            "customer",
            "created_by",
            "payment_method",
        )
        .prefetch_related(
            "items__product"
        )
        .all()
    )

    # =====================================================
    # FILTERING / SEARCH / ORDERING
    # =====================================================

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "branch",
        "status",
        "created_by",
        "customer",
        "payment_method",
        "created_at",
    ]

    search_fields = [
        "invoice_number",
        "customer_name",
        "customer_phone",
        "customer__name",
        "customer__phone",
        "created_by__username",
        "created_by__first_name",
        "created_by__last_name",
    ]

    ordering_fields = [
        "created_at",
        "total",
        "subtotal",
        "discount",
        "tax_amount",
    ]

    ordering = [
        "-created_at"
    ]

    # =====================================================
    # SERIALIZER
    # =====================================================

    def get_serializer_class(self):

        if self.action == "list":
            return SaleListSerializer

        if self.action == "create":
            return SaleCreateSerializer

        if self.action in [
            "update",
            "partial_update",
        ]:
            return SaleUpdateSerializer

        if self.action == "cancel":
            return SaleCancelSerializer

        if self.action == "receipt":
            return SaleReceiptSerializer

        if self.action == "summary":
            return SaleSummarySerializer

        return SaleDetailSerializer

    # =====================================================
    # CHECK CASHIER
    # =====================================================

    def is_cashier(self):

        user = self.request.user

        if not user or not user.is_authenticated:
            return False

        role = getattr(user, "role", None)

        # Role is a ForeignKey/object
        if role is not None:

            role_name = getattr(
                role,
                "name",
                ""
            )

            if str(role_name).strip().lower() == "cashier":
                return True

            # In case your Role model uses "code"
            role_code = getattr(
                role,
                "code",
                ""
            )

            if str(role_code).strip().lower() == "cashier":
                return True

        # In case role is directly stored as a string
        if isinstance(role, str):

            if role.strip().lower() == "cashier":
                return True

        return False

    # =====================================================
    # QUERYSET
    # =====================================================

    def get_queryset(self):

        queryset = super().get_queryset()

        user = self.request.user

        # =================================================
        # CASHIER RESTRICTION
        # =================================================
        #
        # Cashier can ONLY see sales created by herself.
        #
        # Other roles can see all sales.
        #
        # This is enforced on the backend for security.
        # =================================================

        if self.is_cashier():

            queryset = queryset.filter(
                created_by=user
            )

        # =================================================
        # DATE FILTERS
        # =================================================

        start_date = self.request.query_params.get(
            "start_date"
        )

        end_date = self.request.query_params.get(
            "end_date"
        )

        if start_date:

            queryset = queryset.filter(
                created_at__date__gte=start_date
            )

        if end_date:

            queryset = queryset.filter(
                created_at__date__lte=end_date
            )

        return queryset

    # =====================================================
    # RETRIEVE
    # =====================================================

    def retrieve(
        self,
        request,
        *args,
        **kwargs
    ):
        """
        Direct GET /sales/{id}/ is disabled.

        Receipt endpoint remains available.
        """

        return Response(
            {
                "success": False,
                "detail": "Method not allowed.",
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    # =====================================================
    # CREATE SALE
    # =====================================================

    @transaction.atomic
    def create(
        self,
        request,
        *args,
        **kwargs
    ):
        """
        Create a new sale.

        The frontend cannot choose created_by.

        SaleCreateSerializer gets the authenticated user
        from serializer context and stores it as created_by.
        """

        # =================================================
        # AUTHENTICATION
        # =================================================

        if (
            not request.user
            or not request.user.is_authenticated
        ):

            return Response(
                {
                    "success": False,
                    "message": "Authentication required.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # =================================================
        # SERIALIZER
        # =================================================

        serializer = self.get_serializer(
            data=request.data,
            context={
                **self.get_serializer_context(),

                "payment_data": request.data.get(
                    "payment",
                    None
                ),
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        # =================================================
        # SAVE
        # =================================================

        sale = serializer.save()

        # =================================================
        # RESPONSE
        # =================================================

        return Response(
            {
                "success": True,
                "message": "Sale completed successfully.",
                "data": SaleDetailSerializer(
                    sale,
                    context=self.get_serializer_context(),
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )

    # =====================================================
    # CANCEL SALE
    # =====================================================

    @action(
        detail=True,
        methods=["post"],
    )
    @transaction.atomic
    def cancel(
        self,
        request,
        pk=None
    ):
        """
        Cancel a sale and restore stock.

        Cashier can only cancel her own sale because
        get_object() uses the restricted queryset.
        """

        # =================================================
        # AUTHENTICATION
        # =================================================

        if (
            not request.user
            or not request.user.is_authenticated
        ):

            return Response(
                {
                    "success": False,
                    "message": "Authentication required.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # =================================================
        # GET SALE
        # =================================================
        #
        # IMPORTANT:
        # get_object() uses get_queryset().
        #
        # Therefore a cashier cannot cancel another
        # cashier's sale even if she knows the sale ID.
        # =================================================

        sale = self.get_object()

        # =================================================
        # CHECK STATUS
        # =================================================

        if sale.status == "CANCELLED":

            return Response(
                {
                    "success": False,
                    "message": "Sale is already cancelled.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =================================================
        # VALIDATE CANCELLATION
        # =================================================

        serializer = self.get_serializer(
            data=request.data,
            context={
                "request": request,
                "sale": sale,
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        reason = serializer.validated_data.get(
            "reason",
            ""
        )

        # =================================================
        # RESTORE STOCK
        # =================================================

        sale_items = (
            sale.items
            .select_related("product")
            .all()
        )

        for item in sale_items:

            stock = (
                Stock.objects
                .select_for_update()
                .filter(
                    product=item.product,
                    branch=sale.branch,
                )
                .first()
            )

            # =================================================
            # STOCK EXISTS
            # =================================================

            if stock:

                old_quantity = stock.quantity

                stock.quantity += item.quantity

                stock.save(
                    update_fields=[
                        "quantity"
                    ]
                )

                # =================================================
                # STOCK MOVEMENT
                # =================================================

                StockMovement.objects.create(
                    product=item.product,
                    branch=sale.branch,
                    quantity=item.quantity,
                    previous_quantity=old_quantity,
                    new_quantity=stock.quantity,
                    movement_type="RETURN",
                    reference=(
                        f"Cancel Sale "
                        f"{sale.invoice_number}"
                    ),
                    created_by=request.user,
                    notes=reason,
                )

            # =================================================
            # STOCK DOES NOT EXIST
            # =================================================

            else:

                stock = Stock.objects.create(
                    product=item.product,
                    branch=sale.branch,
                    quantity=item.quantity,
                )

                StockMovement.objects.create(
                    product=item.product,
                    branch=sale.branch,
                    quantity=item.quantity,
                    previous_quantity=0,
                    new_quantity=stock.quantity,
                    movement_type="RETURN",
                    reference=(
                        f"Cancel Sale "
                        f"{sale.invoice_number}"
                    ),
                    created_by=request.user,
                    notes=reason,
                )

        # =================================================
        # UPDATE SALE STATUS
        # =================================================

        sale.status = "CANCELLED"

        # =================================================
        # CANCELLATION NOTE
        # =================================================

        cancellation_note = (
            f"Cancelled: {reason}"
            if reason
            else "Sale cancelled."
        )

        existing_notes = (
            sale.notes or ""
        ).strip()

        if existing_notes:

            sale.notes = (
                f"{existing_notes}\n"
                f"{cancellation_note}"
            )

        else:

            sale.notes = cancellation_note

        sale.save(
            update_fields=[
                "status",
                "notes",
            ]
        )

        # =================================================
        # CANCEL PAYMENTS
        # =================================================

        from apps.payments.models import Payment

        Payment.objects.filter(
            sale=sale
        ).update(
            status="CANCELLED"
        )

        # =================================================
        # RESPONSE
        # =================================================

        return Response(
            {
                "success": True,
                "message": "Sale cancelled successfully.",
                "data": SaleDetailSerializer(
                    sale,
                    context=self.get_serializer_context(),
                ).data,
            },
            status=status.HTTP_200_OK,
        )

    # =====================================================
    # RECEIPT
    # =====================================================

    @action(
        detail=True,
        methods=["get"],
    )
    def receipt(
        self,
        request,
        pk=None
    ):
        """
        Return receipt data.

        Cashier can only access receipts belonging
        to her own sales.
        """

        # get_object() respects cashier restriction
        sale = self.get_object()

        serializer = self.get_serializer(
            sale,
            context=self.get_serializer_context(),
        )

        return Response(
            {
                "success": True,
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    # =====================================================
    # SALES SUMMARY
    # =====================================================

    @action(
        detail=False,
        methods=["get"],
    )
    def summary(
        self,
        request
    ):
        """
        Sales summary.

        Cashier:
            Only her own sales.

        Other roles:
            All sales.

        Supports:
            start_date
            end_date
        """

        # =================================================
        # GET FILTERED QUERYSET
        # =================================================

        queryset = self.get_queryset()

        # =================================================
        # COMPLETED SALES
        # =================================================

        completed_sales = queryset.filter(
            status="COMPLETED"
        )

        # =================================================
        # BASIC SUMMARY
        # =================================================

        summary = completed_sales.aggregate(
            total_sales=Sum("total"),
            total_orders=Count("id"),
            total_tax=Sum("tax_amount"),
            total_discount=Sum("discount"),
        )

        total_sales = (
            summary["total_sales"]
            or 0
        )

        total_orders = (
            summary["total_orders"]
            or 0
        )

        total_tax = (
            summary["total_tax"]
            or 0
        )

        total_discount = (
            summary["total_discount"]
            or 0
        )

        # =================================================
        # AVERAGE ORDER VALUE
        # =================================================

        average_order_value = (
            total_sales / total_orders
            if total_orders > 0
            else 0
        )

        # =================================================
        # TOP PRODUCTS
        # =================================================

        top_products = (
            SaleItem.objects
            .filter(
                sale__in=completed_sales
            )
            .values(
                "product__name"
            )
            .annotate(
                total_quantity=Sum(
                    "quantity"
                ),
                total_revenue=Sum(
                    "total"
                ),
            )
            .order_by(
                "-total_revenue"
            )[:10]
        )

        # =================================================
        # SALES BY HOUR
        # =================================================

        seven_days_ago = (
            timezone.now()
            - timedelta(days=7)
        )

        sales_by_hour = (
            completed_sales
            .filter(
                created_at__gte=seven_days_ago
            )
            .values(
                "created_at",
                "total",
            )
        )

        hourly_data = {}

        for sale in sales_by_hour:

            created_at = sale["created_at"]

            if not created_at:
                continue

            hour = created_at.hour

            hour_key = f"{hour:02d}:00"

            hourly_data[hour_key] = (
                hourly_data.get(
                    hour_key,
                    0
                )
                + float(
                    sale["total"] or 0
                )
            )

        # =================================================
        # SALES BY DAY
        # =================================================

        thirty_days_ago = (
            timezone.now()
            - timedelta(days=30)
        )

        daily_sales = (
            completed_sales
            .filter(
                created_at__gte=thirty_days_ago
            )
            .values(
                "created_at",
                "total",
            )
        )

        daily_data = {}

        for sale in daily_sales:

            created_at = sale["created_at"]

            if not created_at:
                continue

            day_key = (
                created_at
                .date()
                .isoformat()
            )

            daily_data[day_key] = (
                daily_data.get(
                    day_key,
                    0
                )
                + float(
                    sale["total"] or 0
                )
            )

        # =================================================
        # PAYMENT METHODS
        # =================================================

        payment_methods = (
            completed_sales
            .values(
                "payment_method"
            )
            .annotate(
                total=Sum("total"),
                count=Count("id"),
            )
            .order_by(
                "-total"
            )
        )

        payment_method_data = {
            item["payment_method"]: {
                "total": float(
                    item["total"] or 0
                ),
                "count": item["count"],
            }
            for item in payment_methods
        }

        # =================================================
        # RESPONSE
        # =================================================

        return Response(
            {
                "success": True,

                "data": {

                    "total_sales": float(
                        total_sales
                    ),

                    "total_orders": int(
                        total_orders
                    ),

                    "average_order_value": float(
                        average_order_value
                    ),

                    "total_tax": float(
                        total_tax
                    ),

                    "total_discount": float(
                        total_discount
                    ),

                    "top_products": list(
                        top_products
                    ),

                    "sales_by_hour": (
                        hourly_data
                    ),

                    "sales_by_day": (
                        daily_data
                    ),

                    "payment_methods": (
                        payment_method_data
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )