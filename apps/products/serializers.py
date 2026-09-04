from rest_framework import serializers

from .models import (
    Category,
    Brand,
    Product,
)

from apps.inventory.models import Stock


# ==========================================================
# CATEGORY SERIALIZER
# ==========================================================

class CategorySerializer(serializers.ModelSerializer):

    parent_name = serializers.CharField(
        source="parent.name",
        read_only=True
    )

    class Meta:
        model = Category

        fields = [
            "id",
            "name",
            "description",
            "parent",
            "parent_name",
            "is_active",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "parent_name",
            "created_at",
        ]


# ==========================================================
# BRAND SERIALIZER
# ==========================================================

class BrandSerializer(serializers.ModelSerializer):

    class Meta:
        model = Brand

        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]


# ==========================================================
# PRODUCT SERIALIZER
# ==========================================================

class ProductSerializer(serializers.ModelSerializer):

    # ======================================================
    # RELATED INFORMATION
    # ======================================================

    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )

    brand_name = serializers.CharField(
        source="brand.name",
        read_only=True
    )

    supplier_name = serializers.CharField(
        source="supplier.name",
        read_only=True
    )

    company_name = serializers.CharField(
        source="company.name",
        read_only=True
    )

    # ======================================================
    # CREATED BY
    # ======================================================

    created_by_name = serializers.SerializerMethodField()

    # ======================================================
    # BRANCH
    # ======================================================

    branch = serializers.IntegerField(
        write_only=True,
        required=False,
        default=1,
        min_value=1
    )

    # ======================================================
    # INITIAL STOCK
    # ======================================================

    stock = serializers.IntegerField(
        write_only=True,
        required=False,
        default=0,
        min_value=0
    )

    # ======================================================
    # CURRENT STOCK
    # ======================================================

    current_stock = serializers.SerializerMethodField()

    # ======================================================
    # META
    # ======================================================

    class Meta:

        model = Product

        fields = [
            "id",
            "name",
            "sku",
            "barcode",

            "category",
            "category_name",

            "brand",
            "brand_name",

            "supplier",
            "supplier_name",

            "branch",

            # Created by
            "created_by",
            "created_by_name",

            "cost_price",
            "selling_price",
            "wholesale_price",

            "tax_rate",

            "description",
            "image",

            "stock",
            "minimum_stock",
            "current_stock",

            "is_active",
            "is_kitchen",

            "company",
            "company_name",

            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",

            "category_name",
            "brand_name",
            "supplier_name",
            "company_name",

            "created_by",
            "created_by_name",

            "current_stock",

            "created_at",
            "updated_at",
        ]

    # ======================================================
    # CREATED BY NAME
    # ======================================================

    def get_created_by_name(self, obj):

        if not obj.created_by:
            return "-"

        return (
            getattr(obj.created_by, "full_name", None)
            or getattr(obj.created_by, "name", None)
            or getattr(obj.created_by, "username", None)
            or str(obj.created_by)
        )

    # ======================================================
    # CREATE PRODUCT
    # ======================================================

    def create(self, validated_data):

        # --------------------------------------------------
        # Get initial stock
        # --------------------------------------------------

        stock_quantity = validated_data.pop(
            "stock",
            0
        )

        # --------------------------------------------------
        # Get branch
        # --------------------------------------------------

        branch_id = validated_data.pop(
            "branch",
            1
        )

        # --------------------------------------------------
        # Get authenticated user
        # --------------------------------------------------

        request = self.context.get("request")

        if request and request.user.is_authenticated:

            validated_data["created_by"] = request.user

        # --------------------------------------------------
        # Create product
        # --------------------------------------------------

        product = Product.objects.create(
            **validated_data
        )

        # --------------------------------------------------
        # Create stock record
        # --------------------------------------------------

        Stock.objects.create(
            product=product,
            branch_id=branch_id,
            quantity=stock_quantity
        )

        return product

    # ======================================================
    # UPDATE PRODUCT
    # ======================================================

    def update(self, instance, validated_data):

        stock_quantity = validated_data.pop(
            "stock",
            None
        )

        branch_id = validated_data.pop(
            "branch",
            None
        )

        # --------------------------------------------------
        # Update product
        # --------------------------------------------------

        instance = super().update(
            instance,
            validated_data
        )

        # --------------------------------------------------
        # Update stock only if explicitly provided
        # --------------------------------------------------

        if stock_quantity is not None:

            if branch_id is None:

                stock = Stock.objects.filter(
                    product=instance
                ).first()

                if stock:

                    stock.quantity = stock_quantity

                    stock.save(
                        update_fields=["quantity"]
                    )

            else:

                stock, created = Stock.objects.get_or_create(
                    product=instance,
                    branch_id=branch_id,
                    defaults={
                        "quantity": stock_quantity
                    }
                )

                if not created:

                    stock.quantity = stock_quantity

                    stock.save(
                        update_fields=["quantity"]
                    )

        return instance

    # ======================================================
    # CURRENT STOCK
    # ======================================================

    def get_current_stock(self, obj):

        return obj.get_current_stock()