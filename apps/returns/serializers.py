from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers

from .models import Return, ReturnItem


# =========================================================
# RETURN ITEM SERIALIZER
# =========================================================

class ReturnItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    class Meta:
        model = ReturnItem

        fields = [
            "id",
            "sale_item",
            "product",
            "product_name",
            "quantity",
            "unit_price",
            "subtotal",
        ]

        read_only_fields = [
            "id",
            "product",
            "product_name",
            "unit_price",
            "subtotal",
        ]


# =========================================================
# RETURN SERIALIZER
# =========================================================

class ReturnSerializer(serializers.ModelSerializer):

    items = ReturnItemSerializer(
        many=True
    )

    customer_name = serializers.CharField(
        source="customer.name",
        read_only=True,
    )

    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Return

        fields = [
            "id",
            "return_number",
            "sale",
            "customer",
            "customer_name",
            "branch",
            "reason",
            "notes",
            "refund_method",
            "refund_amount",
            "status",
            "created_by",
            "created_by_name",
            "approved_by",
            "created_at",
            "approved_at",
            "completed_at",
            "items",
        ]

        read_only_fields = [
            "id",
            "return_number",
            "customer",
            "branch",
            "refund_amount",
            "status",
            "created_by",
            "created_by_name",
            "approved_by",
            "created_at",
            "approved_at",
            "completed_at",
        ]

    # =====================================================
    # CREATED BY NAME
    # =====================================================

    def get_created_by_name(self, obj):
        if not obj.created_by:
            return None

        return (
            obj.created_by.get_full_name()
            or obj.created_by.username
        )

    # =====================================================
    # VALIDATE SALE
    # =====================================================

    def validate(self, attrs):
        sale = attrs.get("sale")

        if not sale:
            raise serializers.ValidationError({
                "sale": "Sale is required."
            })

        # -------------------------------------------------
        # Normalize status
        # -------------------------------------------------

        sale_status = str(
            getattr(
                sale,
                "status",
                ""
            )
        ).strip().lower()

        # -------------------------------------------------
        # Only completed / paid sales can be returned
        # -------------------------------------------------

        allowed_statuses = {
            "completed",
            "paid",
        }

        if sale_status not in allowed_statuses:
            raise serializers.ValidationError({
                "sale": (
                    "Only completed or paid sales "
                    "can be returned. "
                    f"Current sale status: "
                    f"{getattr(sale, 'status', '-')}"
                )
            })

        # -------------------------------------------------
        # Sale must have a branch
        # -------------------------------------------------

        if not getattr(
            sale,
            "branch_id",
            None
        ):
            raise serializers.ValidationError({
                "sale": (
                    "The selected sale does not "
                    "have a branch."
                )
            })

        return attrs

    # =====================================================
    # VALIDATE ITEMS
    # =====================================================

    def validate_items(self, items):

        if not items:
            raise serializers.ValidationError(
                "At least one item is required."
            )

        for item in items:

            # ---------------------------------------------
            # Sale item
            # ---------------------------------------------

            sale_item = item.get(
                "sale_item"
            )

            if not sale_item:
                raise serializers.ValidationError(
                    "Each return item must have a sale item."
                )

            # ---------------------------------------------
            # Quantity
            # ---------------------------------------------

            quantity = Decimal(
                str(
                    item.get(
                        "quantity",
                        "0"
                    )
                )
            )

            if quantity <= 0:
                raise serializers.ValidationError(
                    "Return quantity must be greater than zero."
                )

        return items

    # =====================================================
    # CREATE RETURN
    # =====================================================

    @transaction.atomic
    def create(self, validated_data):

        # -------------------------------------------------
        # Extract nested items
        # -------------------------------------------------

        items_data = validated_data.pop(
            "items"
        )

        # -------------------------------------------------
        # Request / user
        # -------------------------------------------------

        request = self.context.get(
            "request"
        )

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError({
                "created_by": (
                    "Authenticated user is required "
                    "to create a return."
                )
            })

        # -------------------------------------------------
        # Sale
        # -------------------------------------------------

        sale = validated_data.get(
            "sale"
        )

        if not sale:
            raise serializers.ValidationError({
                "sale": "Sale is required."
            })

        # -------------------------------------------------
        # Customer
        # -------------------------------------------------

        customer = getattr(
            sale,
            "customer",
            None
        )

        # -------------------------------------------------
        # Branch
        # -------------------------------------------------

        branch = getattr(
            sale,
            "branch",
            None
        )

        if not branch:
            raise serializers.ValidationError({
                "sale": (
                    "The selected sale does not "
                    "have a branch."
                )
            })

        # -------------------------------------------------
        # Create return record
        # -------------------------------------------------

        return_record = Return.objects.create(
            created_by=request.user,
            customer=customer,
            branch=branch,
            **validated_data,
        )

        total = Decimal("0.00")

        # =================================================
        # PROCESS RETURN ITEMS
        # =================================================

        for item_data in items_data:

            sale_item = item_data.get(
                "sale_item"
            )

            quantity = Decimal(
                str(
                    item_data.get(
                        "quantity",
                        "0"
                    )
                )
            )

            # ---------------------------------------------
            # Validate sale item
            # ---------------------------------------------

            if not sale_item:
                raise serializers.ValidationError({
                    "items": (
                        "A valid sale item is required."
                    )
                })

            # ---------------------------------------------
            # Ensure item belongs to selected sale
            # ---------------------------------------------

            if sale_item.sale_id != sale.id:
                raise serializers.ValidationError({
                    "items": (
                        f"Sale item {sale_item.id} "
                        "does not belong to the "
                        "selected sale."
                    )
                })

            # ---------------------------------------------
            # Validate quantity
            # ---------------------------------------------

            if quantity <= 0:
                raise serializers.ValidationError({
                    "items": (
                        f"Return quantity for "
                        f"{sale_item.product.name} "
                        "must be greater than zero."
                    )
                })

            # ---------------------------------------------
            # Original sold quantity
            # ---------------------------------------------

            sold_quantity = Decimal(
                str(
                    sale_item.quantity
                )
            )

            # ---------------------------------------------
            # Previously returned quantity
            #
            # Only APPROVED and COMPLETED returns
            # consume returnable quantity.
            #
            # PENDING / REJECTED do not.
            # ---------------------------------------------

            already_returned = (
                ReturnItem.objects
                .filter(
                    sale_item=sale_item,
                    return_record__status__in=[
                        Return.STATUS_APPROVED,
                        Return.STATUS_COMPLETED,
                    ],
                )
                .aggregate(
                    total=Sum("quantity")
                )
                .get("total")
                or Decimal("0")
            )

            already_returned = Decimal(
                str(already_returned)
            )

            # ---------------------------------------------
            # Remaining quantity
            # ---------------------------------------------

            remaining = (
                sold_quantity
                - already_returned
            )

            # ---------------------------------------------
            # Prevent negative remaining quantity
            # ---------------------------------------------

            if remaining < 0:
                remaining = Decimal("0")

            # ---------------------------------------------
            # Requested quantity cannot exceed remaining
            # ---------------------------------------------

            if quantity > remaining:
                raise serializers.ValidationError({
                    "items": (
                        f"Cannot return {quantity} "
                        f"of {sale_item.product.name}. "
                        f"Only {remaining} "
                        "remains returnable."
                    )
                })

            # ---------------------------------------------
            # Unit price
            # ---------------------------------------------

            unit_price = Decimal(
                str(
                    sale_item.unit_price
                )
            )

            # ---------------------------------------------
            # Calculate subtotal
            # ---------------------------------------------

            subtotal = (
                quantity *
                unit_price
            )

            # ---------------------------------------------
            # Create return item
            # ---------------------------------------------

            ReturnItem.objects.create(
                return_record=return_record,
                sale_item=sale_item,
                product=sale_item.product,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal,
            )

            # ---------------------------------------------
            # Add to refund total
            # ---------------------------------------------

            total += subtotal

        # =================================================
        # VALIDATE TOTAL
        # =================================================

        if total <= 0:
            raise serializers.ValidationError({
                "items": (
                    "The total return amount "
                    "must be greater than zero."
                )
            })

        # =================================================
        # SAVE REFUND AMOUNT
        # =================================================

        return_record.refund_amount = total

        return_record.save(
            update_fields=[
                "refund_amount"
            ]
        )

        return return_record