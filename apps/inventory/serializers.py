from rest_framework import serializers

from .models import Stock, StockMovement


class StockSerializer(serializers.ModelSerializer):
    # Product details
    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )
    product_sku = serializers.CharField(
        source="product.sku",
        read_only=True,
    )

    # Category details; a product may have no category
    category_id = serializers.IntegerField(
        source="product.category.id",
        read_only=True,
        allow_null=True,
    )
    category_name = serializers.CharField(
        source="product.category.name",
        read_only=True,
        allow_null=True,
    )

    # Branch details
    branch_name = serializers.CharField(
        source="branch.name",
        read_only=True,
    )

    # Product pricing
    cost_price = serializers.DecimalField(
        source="product.cost_price",
        max_digits=15,
        decimal_places=2,
        read_only=True,
    )
    selling_price = serializers.DecimalField(
        source="product.selling_price",
        max_digits=15,
        decimal_places=2,
        read_only=True,
    )

    # Available stock after reservations
    available_quantity = serializers.SerializerMethodField()

    def get_available_quantity(self, obj):
        return max(
            0,
            obj.quantity - obj.reserved_quantity,
        )

    class Meta:
        model = Stock

        fields = [
            "id",
            "product",
            "product_name",
            "product_sku",
            "category_id",
            "category_name",
            "branch",
            "branch_name",
            "quantity",
            "reserved_quantity",
            "available_quantity",
            "min_quantity",
            "max_quantity",
            "cost_price",
            "selling_price",
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
            "available_quantity",
            "cost_price",
            "selling_price",
        ]

    def validate(self, attrs):
        product = attrs.get("product")
        branch = attrs.get("branch")

        if self.instance:
            product = product or self.instance.product
            branch = branch or self.instance.branch

        if product and branch:
            queryset = Stock.objects.filter(
                product=product,
                branch=branch,
            )

            if self.instance:
                queryset = queryset.exclude(
                    pk=self.instance.pk
                )

            if queryset.exists():
                raise serializers.ValidationError({
                    "product": (
                        "Stock already exists for this product "
                        "and branch."
                    )
                })

        return attrs


class StockMovementSerializer(serializers.ModelSerializer):
    # Product details
    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )
    product_sku = serializers.CharField(
        source="product.sku",
        read_only=True,
    )

    # Branch details
    branch_name = serializers.CharField(
        source="branch.name",
        read_only=True,
    )

    # User details
    created_by_name = serializers.SerializerMethodField()

    def get_created_by_name(self, obj):
        if not obj.created_by:
            return None

        full_name = getattr(
            obj.created_by,
            "get_full_name",
            None,
        )

        if callable(full_name):
            name = full_name()
            if name:
                return name

        return (
            getattr(obj.created_by, "username", None)
            or str(obj.created_by)
        )

    class Meta:
        model = StockMovement

        fields = [
            "id",
            "product",
            "product_name",
            "product_sku",
            "branch",
            "branch_name",
            "quantity",
            "previous_quantity",
            "new_quantity",
            "movement_type",
            "reference",
            "notes",
            "created_by",
            "created_by_name",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "product_name",
            "product_sku",
            "branch_name",
            "created_by",
            "created_by_name",
            "previous_quantity",
            "new_quantity",
            "created_at",
        ]