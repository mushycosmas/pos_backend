from rest_framework import serializers

from .models import Stock, StockMovement


# =========================================================
# STOCK SERIALIZER
# =========================================================

class StockSerializer(serializers.ModelSerializer):

    # -----------------------------------------------------
    # PRODUCT
    # -----------------------------------------------------

    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )

    product_sku = serializers.CharField(
        source="product.sku",
        read_only=True
    )

    # -----------------------------------------------------
    # BRANCH
    # -----------------------------------------------------

    branch_name = serializers.CharField(
        source="branch.name",
        read_only=True
    )

    # -----------------------------------------------------
    # CATEGORY
    # -----------------------------------------------------

    category_id = serializers.IntegerField(
        source="product.category.id",
        read_only=True
    )

    category_name = serializers.CharField(
        source="product.category.name",
        read_only=True
    )

    # -----------------------------------------------------
    # PRODUCT PRICES
    # -----------------------------------------------------

    cost_price = serializers.DecimalField(
        source="product.cost_price",
        max_digits=15,
        decimal_places=2,
        read_only=True
    )

    selling_price = serializers.DecimalField(
        source="product.selling_price",
        max_digits=15,
        decimal_places=2,
        read_only=True
    )

    class Meta:

        model = Stock

        fields = [
            # Stock
            "id",

            # Product
            "product",
            "product_name",
            "product_sku",

            # Category
            "category_id",
            "category_name",

            # Branch
            "branch",
            "branch_name",

            # Stock quantities
            "quantity",
            "reserved_quantity",
            "min_quantity",
            "max_quantity",

            # Product prices
            "cost_price",
            "selling_price",

            # Dates
            "last_updated",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "last_updated",
            "created_at",
            "product_name",
            "product_sku",
            "category_id",
            "category_name",
            "branch_name",
            "cost_price",
            "selling_price",
        ]


# =========================================================
# STOCK MOVEMENT SERIALIZER
# =========================================================

class StockMovementSerializer(serializers.ModelSerializer):

    # -----------------------------------------------------
    # PRODUCT
    # -----------------------------------------------------

    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )

    product_sku = serializers.CharField(
        source="product.sku",
        read_only=True
    )

    # -----------------------------------------------------
    # BRANCH
    # -----------------------------------------------------

    branch_name = serializers.CharField(
        source="branch.name",
        read_only=True
    )

    # -----------------------------------------------------
    # USER
    # -----------------------------------------------------

    created_by_name = serializers.SerializerMethodField()

    def get_created_by_name(self, obj):
        if not obj.created_by:
            return None

        return (
            getattr(obj.created_by, "get_full_name", lambda: "")()
            or getattr(obj.created_by, "username", None)
            or str(obj.created_by)
        )

    class Meta:

        model = StockMovement

        fields = [
            # Movement
            "id",

            # Product
            "product",
            "product_name",
            "product_sku",

            # Branch
            "branch",
            "branch_name",

            # Quantities
            "quantity",
            "previous_quantity",
            "new_quantity",

            # Movement information
            "movement_type",
            "reference",
            "notes",

            # User
            "created_by",
            "created_by_name",

            # Date
            "created_at",
        ]

        read_only_fields = [
            "id",
            "product_name",
            "product_sku",
            "branch_name",
            "created_by_name",
            "created_at",
            "previous_quantity",
            "new_quantity",
        ]