from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from rest_framework import serializers

from .models import (
    Purchase,
    PurchaseItem,
)


# ==============================================================
# MONEY HELPER
# ==============================================================

def money(value):

    return Decimal(
        str(value or 0)
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


# ==============================================================
# PURCHASE ITEM SERIALIZER
# ==============================================================

class PurchaseItemSerializer(
    serializers.ModelSerializer
):

    # ----------------------------------------------------------
    # PRODUCT NAME
    # ----------------------------------------------------------

    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )

    # ----------------------------------------------------------
    # REMAINING QUANTITY
    # ----------------------------------------------------------

    remaining_quantity = serializers.SerializerMethodField()

    # ----------------------------------------------------------
    # FULLY RECEIVED
    # ----------------------------------------------------------

    is_fully_received = serializers.SerializerMethodField()

    # ----------------------------------------------------------
    # PARTIALLY RECEIVED
    # ----------------------------------------------------------

    is_partially_received = (
        serializers.SerializerMethodField()
    )

    # ==========================================================
    # META
    # ==========================================================

    class Meta:

        model = PurchaseItem

        fields = [
            "id",
            "purchase",

            "product",
            "product_name",

            "quantity",
            "received_quantity",
            "remaining_quantity",

            "is_fully_received",
            "is_partially_received",

            "unit_cost",

            "discount",
            "tax",

            "total",

            "created_at",
        ]

        read_only_fields = [
            "id",
            "purchase",

            "product_name",

            "received_quantity",
            "remaining_quantity",

            "is_fully_received",
            "is_partially_received",

            "total",

            "created_at",
        ]

    # ==========================================================
    # REMAINING
    # ==========================================================

    def get_remaining_quantity(
        self,
        obj
    ):

        return max(
            0,
            obj.quantity - obj.received_quantity
        )

    # ==========================================================
    # FULLY RECEIVED
    # ==========================================================

    def get_is_fully_received(
        self,
        obj
    ):

        return (
            obj.received_quantity
            >=
            obj.quantity
        )

    # ==========================================================
    # PARTIALLY RECEIVED
    # ==========================================================

    def get_is_partially_received(
        self,
        obj
    ):

        return (
            obj.received_quantity > 0
            and
            obj.received_quantity < obj.quantity
        )

    # ==========================================================
    # VALIDATION
    # ==========================================================

    def validate_quantity(
        self,
        value
    ):

        if value <= 0:

            raise serializers.ValidationError(
                "Quantity must be greater than 0."
            )

        return value

    # ----------------------------------------------------------

    def validate_unit_cost(
        self,
        value
    ):

        if value < 0:

            raise serializers.ValidationError(
                "Unit cost cannot be negative."
            )

        return value

    # ----------------------------------------------------------

    def validate_discount(
        self,
        value
    ):

        if value < 0:

            raise serializers.ValidationError(
                "Discount cannot be negative."
            )

        if value > 100:

            raise serializers.ValidationError(
                "Discount cannot be greater than 100%."
            )

        return value

    # ----------------------------------------------------------

    def validate_tax(
        self,
        value
    ):

        if value < 0:

            raise serializers.ValidationError(
                "Tax cannot be negative."
            )

        if value > 100:

            raise serializers.ValidationError(
                "Tax cannot be greater than 100%."
            )

        return value

    # ==========================================================
    # CALCULATE TOTAL
    # ==========================================================

    @staticmethod
    def calculate_total(
        quantity,
        unit_cost,
        discount,
        tax
    ):

        quantity = Decimal(
            str(quantity)
        )

        unit_cost = Decimal(
            str(unit_cost)
        )

        discount = Decimal(
            str(discount or 0)
        )

        tax = Decimal(
            str(tax or 0)
        )

        # ------------------------------------------------------
        # GROSS
        # ------------------------------------------------------

        gross = (
            quantity *
            unit_cost
        )

        # ------------------------------------------------------
        # DISCOUNT
        # ------------------------------------------------------

        discount_amount = (
            gross *
            discount /
            Decimal("100")
        )

        # ------------------------------------------------------
        # TAXABLE
        # ------------------------------------------------------

        taxable_amount = (
            gross -
            discount_amount
        )

        # ------------------------------------------------------
        # TAX
        # ------------------------------------------------------

        tax_amount = (
            taxable_amount *
            tax /
            Decimal("100")
        )

        # ------------------------------------------------------
        # FINAL
        # ------------------------------------------------------

        total = (
            taxable_amount +
            tax_amount
        )

        return money(total)

    # ==========================================================
    # CREATE
    # ==========================================================

    def create(
        self,
        validated_data
    ):

        validated_data["total"] = (
            self.calculate_total(
                quantity=validated_data[
                    "quantity"
                ],

                unit_cost=validated_data[
                    "unit_cost"
                ],

                discount=validated_data.get(
                    "discount",
                    Decimal("0")
                ),

                tax=validated_data.get(
                    "tax",
                    Decimal("0")
                ),
            )
        )

        # ------------------------------------------------------
        # Always start with zero received.
        #
        # Receiving must happen through the
        # Purchase receive endpoint.
        # ------------------------------------------------------

        validated_data[
            "received_quantity"
        ] = 0

        return super().create(
            validated_data
        )

    # ==========================================================
    # UPDATE
    # ==========================================================

    def update(
        self,
        instance,
        validated_data
    ):

        quantity = validated_data.get(
            "quantity",
            instance.quantity
        )

        unit_cost = validated_data.get(
            "unit_cost",
            instance.unit_cost
        )

        discount = validated_data.get(
            "discount",
            instance.discount
        )

        tax = validated_data.get(
            "tax",
            instance.tax
        )

        # ------------------------------------------------------
        # Do not allow changing received_quantity directly.
        # ------------------------------------------------------

        validated_data.pop(
            "received_quantity",
            None
        )

        # ------------------------------------------------------
        # Prevent reducing quantity below received quantity.
        # ------------------------------------------------------

        if quantity < instance.received_quantity:

            raise serializers.ValidationError(
                {
                    "quantity": (
                        "Quantity cannot be less than "
                        "already received quantity."
                    )
                }
            )

        # ------------------------------------------------------
        # Calculate total.
        # ------------------------------------------------------

        validated_data["total"] = (
            self.calculate_total(
                quantity=quantity,
                unit_cost=unit_cost,
                discount=discount,
                tax=tax,
            )
        )

        return super().update(
            instance,
            validated_data
        )


# ==============================================================
# PURCHASE SERIALIZER
# ==============================================================

class PurchaseSerializer(
    serializers.ModelSerializer
):

    # ----------------------------------------------------------
    # SUPPLIER NAME
    # ----------------------------------------------------------

    supplier_name = serializers.CharField(
        source="supplier.name",
        read_only=True
    )

    # ----------------------------------------------------------
    # BRANCH NAME
    # ----------------------------------------------------------

    branch_name = serializers.CharField(
        source="branch.name",
        read_only=True
    )

    # ----------------------------------------------------------
    # COMPANY NAME
    # ----------------------------------------------------------

    company_name = serializers.CharField(
        source="company.name",
        read_only=True
    )

    # ----------------------------------------------------------
    # CREATED BY NAME
    # ----------------------------------------------------------

    created_by_name = serializers.SerializerMethodField()

    # ----------------------------------------------------------
    # ITEMS
    # ----------------------------------------------------------

    items = PurchaseItemSerializer(
        many=True,
        required=False
    )

    # ----------------------------------------------------------
    # TOTAL ORDERED
    # ----------------------------------------------------------

    total_ordered_quantity = (
        serializers.SerializerMethodField()
    )

    # ----------------------------------------------------------
    # TOTAL RECEIVED
    # ----------------------------------------------------------

    total_received_quantity = (
        serializers.SerializerMethodField()
    )

    # ----------------------------------------------------------
    # TOTAL REMAINING
    # ----------------------------------------------------------

    total_remaining_quantity = (
        serializers.SerializerMethodField()
    )

    # ----------------------------------------------------------
    # FULLY RECEIVED
    # ----------------------------------------------------------

    is_fully_received = (
        serializers.SerializerMethodField()
    )

    # ==========================================================
    # META
    # ==========================================================

    class Meta:

        model = Purchase

        fields = [
            "id",

            "purchase_number",

            "supplier",
            "supplier_name",

            "branch",
            "branch_name",

            "company",
            "company_name",

            "order_date",
            "expected_delivery_date",
            "received_date",

            "subtotal",
            "discount",
            "tax",
            "shipping_cost",
            "total",

            "status",
            "payment_status",

            "notes",

            # --------------------------------------------------
            # CREATED BY
            # --------------------------------------------------

            "created_by",
            "created_by_name",

            "items",

            "total_ordered_quantity",
            "total_received_quantity",
            "total_remaining_quantity",
            "is_fully_received",

            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "purchase_number",

            "supplier_name",
            "branch_name",
            "company_name",

            # --------------------------------------------------
            # CREATED BY
            # --------------------------------------------------

            "created_by",
            "created_by_name",

            "subtotal",
            "tax",
            "total",

            "received_date",

            "total_ordered_quantity",
            "total_received_quantity",
            "total_remaining_quantity",
            "is_fully_received",

            "created_at",
            "updated_at",
        ]

    # ==========================================================
    # CREATED BY NAME
    # ==========================================================

    def get_created_by_name(
        self,
        obj
    ):

        if not obj.created_by:
            return "-"

        return (
            getattr(
                obj.created_by,
                "full_name",
                None
            )
            or
            getattr(
                obj.created_by,
                "name",
                None
            )
            or
            getattr(
                obj.created_by,
                "username",
                None
            )
            or
            str(obj.created_by)
        )

    # ==========================================================
    # TOTAL ORDERED
    # ==========================================================

    def get_total_ordered_quantity(
        self,
        obj
    ):

        return sum(
            item.quantity
            for item in obj.items.all()
        )

    # ==========================================================
    # TOTAL RECEIVED
    # ==========================================================

    def get_total_received_quantity(
        self,
        obj
    ):

        return sum(
            item.received_quantity
            for item in obj.items.all()
        )

    # ==========================================================
    # TOTAL REMAINING
    # ==========================================================

    def get_total_remaining_quantity(
        self,
        obj
    ):

        return max(
            0,
            self.get_total_ordered_quantity(obj)
            -
            self.get_total_received_quantity(obj)
        )

    # ==========================================================
    # FULLY RECEIVED
    # ==========================================================

    def get_is_fully_received(
        self,
        obj
    ):

        ordered = (
            self.get_total_ordered_quantity(obj)
        )

        received = (
            self.get_total_received_quantity(obj)
        )

        return (
            ordered > 0
            and
            received >= ordered
        )

    # ==========================================================
    # VALIDATE STATUS
    # ==========================================================

    def validate_status(
        self,
        value
    ):

        # ------------------------------------------------------
        # Do NOT allow an existing purchase to be manually
        # changed to received.
        #
        # It must go through /receive/
        # ------------------------------------------------------

        if (
            self.instance is not None
            and
            value == "received"
            and
            self.instance.status != "received"
        ):

            raise serializers.ValidationError(
                "Use the Receive Purchase action "
                "to mark a purchase as received."
            )

        return value

    # ==========================================================
    # CREATE PURCHASE
    # ==========================================================

    @transaction.atomic
    def create(
        self,
        validated_data
    ):

        # ------------------------------------------------------
        # ITEMS
        # ------------------------------------------------------

        items_data = validated_data.pop(
            "items",
            []
        )

        # ------------------------------------------------------
        # CREATED BY
        # ------------------------------------------------------
        #
        # The frontend must NOT provide created_by.
        #
        # The backend determines the creator from the
        # authenticated request.
        #
        # ------------------------------------------------------

        request = self.context.get(
            "request"
        )

        if (
            request is not None
            and
            request.user.is_authenticated
        ):

            validated_data["created_by"] = (
                request.user
            )

        # ------------------------------------------------------
        # REQUESTED STATUS
        # ------------------------------------------------------

        requested_status = validated_data.get(
            "status",
            "draft"
        )

        should_receive = (
            requested_status == "received"
        )

        if should_receive:

            validated_data["status"] = "ordered"

        # ------------------------------------------------------
        # CREATE PURCHASE
        # ------------------------------------------------------

        purchase = Purchase.objects.create(
            **validated_data
        )

        subtotal = Decimal("0")
        total_tax = Decimal("0")

        # ======================================================
        # CREATE ITEMS
        # ======================================================

        for item_data in items_data:

            quantity = Decimal(
                str(
                    item_data.get(
                        "quantity",
                        0
                    )
                )
            )

            unit_cost = Decimal(
                str(
                    item_data.get(
                        "unit_cost",
                        0
                    )
                )
            )

            discount = Decimal(
                str(
                    item_data.get(
                        "discount",
                        0
                    )
                )
            )

            tax_rate = Decimal(
                str(
                    item_data.get(
                        "tax",
                        0
                    )
                )
            )

            # --------------------------------------------------
            # GROSS
            # --------------------------------------------------

            gross = (
                quantity *
                unit_cost
            )

            # --------------------------------------------------
            # DISCOUNT
            # --------------------------------------------------

            discount_amount = (
                gross *
                discount /
                Decimal("100")
            )

            # --------------------------------------------------
            # TAXABLE
            # --------------------------------------------------

            taxable_amount = (
                gross -
                discount_amount
            )

            # --------------------------------------------------
            # TAX
            # --------------------------------------------------

            tax_amount = (
                taxable_amount *
                tax_rate /
                Decimal("100")
            )

            # --------------------------------------------------
            # TOTAL
            # --------------------------------------------------

            item_total = money(
                taxable_amount +
                tax_amount
            )

            # --------------------------------------------------
            # CREATE ITEM
            # --------------------------------------------------

            PurchaseItem.objects.create(
                purchase=purchase,

                product=item_data[
                    "product"
                ],

                quantity=int(
                    quantity
                ),

                # NEVER trust received_quantity
                # from create request.
                received_quantity=0,

                unit_cost=unit_cost,

                discount=discount,

                tax=tax_rate,

                total=item_total,
            )

            # --------------------------------------------------
            # TOTALS
            # --------------------------------------------------

            subtotal += taxable_amount

            total_tax += tax_amount

        # ======================================================
        # PURCHASE TOTAL
        # ======================================================

        shipping_cost = Decimal(
            str(
                purchase.shipping_cost or 0
            )
        )

        purchase_discount = Decimal(
            str(
                purchase.discount or 0
            )
        )

        purchase.subtotal = money(
            subtotal
        )

        purchase.tax = money(
            total_tax
        )

        purchase.total = money(
            subtotal
            +
            total_tax
            +
            shipping_cost
            -
            purchase_discount
        )

        purchase.save(
            update_fields=[
                "subtotal",
                "tax",
                "total",
                "updated_at",
            ]
        )

        # ======================================================
        # AUTO RECEIVE IF CREATED AS RECEIVED
        # ======================================================

        if should_receive:

            user = None

            if (
                request is not None
                and
                request.user.is_authenticated
            ):

                user = request.user

            purchase.receive(
                user=user
            )

            purchase.refresh_from_db()

        return purchase

    # ==========================================================
    # UPDATE PURCHASE
    # ==========================================================

    @transaction.atomic
    def update(
        self,
        instance,
        validated_data
    ):

        # ------------------------------------------------------
        # ITEMS
        # ------------------------------------------------------

        items_data = validated_data.pop(
            "items",
            None
        )

        # ------------------------------------------------------
        # CREATED BY PROTECTION
        # ------------------------------------------------------
        #
        # Even if somebody manually attempts to send
        # created_by during an update, ignore it.
        #
        # ------------------------------------------------------

        validated_data.pop(
            "created_by",
            None
        )

        # ------------------------------------------------------
        # PROTECT RECEIVED PURCHASES
        # ------------------------------------------------------

        if (
            instance.status == "received"
            and
            items_data is not None
        ):

            raise serializers.ValidationError(
                {
                    "items": (
                        "A fully received purchase "
                        "cannot have its items replaced."
                    )
                }
            )

        # ======================================================
        # UPDATE PURCHASE
        # ======================================================

        for attr, value in validated_data.items():

            setattr(
                instance,
                attr,
                value
            )

        instance.save()

        # ======================================================
        # UPDATE ITEMS
        # ======================================================

        if items_data is not None:

            subtotal = Decimal("0")
            total_tax = Decimal("0")

            # --------------------------------------------------
            # DELETE EXISTING ITEMS
            # --------------------------------------------------

            instance.items.all().delete()

            # ==================================================
            # CREATE NEW ITEMS
            # ==================================================

            for item_data in items_data:

                quantity = Decimal(
                    str(
                        item_data.get(
                            "quantity",
                            0
                        )
                    )
                )

                unit_cost = Decimal(
                    str(
                        item_data.get(
                            "unit_cost",
                            0
                        )
                    )
                )

                discount = Decimal(
                    str(
                        item_data.get(
                            "discount",
                            0
                        )
                    )
                )

                tax_rate = Decimal(
                    str(
                        item_data.get(
                            "tax",
                            0
                        )
                    )
                )

                # ------------------------------------------------
                # GROSS
                # ------------------------------------------------

                gross = (
                    quantity *
                    unit_cost
                )

                # ------------------------------------------------
                # DISCOUNT
                # ------------------------------------------------

                discount_amount = (
                    gross *
                    discount /
                    Decimal("100")
                )

                # ------------------------------------------------
                # TAXABLE
                # ------------------------------------------------

                taxable_amount = (
                    gross -
                    discount_amount
                )

                # ------------------------------------------------
                # TAX
                # ------------------------------------------------

                tax_amount = (
                    taxable_amount *
                    tax_rate /
                    Decimal("100")
                )

                # ------------------------------------------------
                # TOTAL
                # ------------------------------------------------

                item_total = money(
                    taxable_amount +
                    tax_amount
                )

                # ------------------------------------------------
                # CREATE ITEM
                # ------------------------------------------------

                PurchaseItem.objects.create(
                    purchase=instance,

                    product=item_data[
                        "product"
                    ],

                    quantity=int(
                        quantity
                    ),

                    # Never restore received quantity
                    # from frontend.
                    received_quantity=0,

                    unit_cost=unit_cost,

                    discount=discount,

                    tax=tax_rate,

                    total=item_total,
                )

                # ------------------------------------------------
                # TOTALS
                # ------------------------------------------------

                subtotal += taxable_amount

                total_tax += tax_amount

            # ==================================================
            # PURCHASE TOTALS
            # ==================================================

            shipping_cost = Decimal(
                str(
                    instance.shipping_cost or 0
                )
            )

            purchase_discount = Decimal(
                str(
                    instance.discount or 0
                )
            )

            instance.subtotal = money(
                subtotal
            )

            instance.tax = money(
                total_tax
            )

            instance.total = money(
                subtotal
                +
                total_tax
                +
                shipping_cost
                -
                purchase_discount
            )

            instance.save(
                update_fields=[
                    "subtotal",
                    "tax",
                    "total",
                    "updated_at",
                ]
            )

        return instance