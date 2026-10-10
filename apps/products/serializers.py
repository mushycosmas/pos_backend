from django.db import transaction
from django.db.models import Sum

from rest_framework import serializers

from .models import Category, Brand, Product
from apps.inventory.models import Stock
from apps.branches.models import Branch


# ==========================================================
# CATEGORY SERIALIZER
# ==========================================================

class CategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(
        source="parent.name",
        read_only=True,
        allow_null=True,
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
    # Related information
    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
        allow_null=True,
    )

    brand_name = serializers.CharField(
        source="brand.name",
        read_only=True,
        allow_null=True,
    )

    supplier_name = serializers.CharField(
        source="supplier.name",
        read_only=True,
        allow_null=True,
    )

    company_name = serializers.CharField(
        source="company.name",
        read_only=True,
        allow_null=True,
    )

    created_by_name = serializers.SerializerMethodField()

    # Inventory fields: these are not fields on Product.
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(),
        write_only=True,
        required=False,
    )

    stock = serializers.IntegerField(
        write_only=True,
        required=False,
        min_value=0,
    )

    current_stock = serializers.SerializerMethodField()

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

    # ------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------

    def get_request(self):
        return self.context.get("request")

    def get_user_company(self):
        request = self.get_request()

        if not request or not request.user.is_authenticated:
            return None

        return getattr(request.user, "company", None)

    def get_context_branch(self):
        """
        Optional branch context supplied by the viewset.
        Supports a Branch object or a branch ID.
        """
        branch = self.context.get("current_branch")

        if branch is None:
            return None

        if isinstance(branch, Branch):
            return branch

        try:
            return Branch.objects.get(pk=branch)
        except (Branch.DoesNotExist, ValueError, TypeError):
            raise serializers.ValidationError({
                "branch": "The selected branch does not exist."
            })

    def resolve_branch(self, validated_data=None):
        validated_data = validated_data or {}

        branch = validated_data.get("branch")

        if branch is not None:
            return branch

        return self.get_context_branch()

    def validate_branch(self, branch):
        company = self.get_user_company()

        if company is not None:
            branch_company_id = getattr(branch, "company_id", None)

            if (
                branch_company_id is not None
                and branch_company_id != company.pk
            ):
                raise serializers.ValidationError(
                    "This branch does not belong to your company."
                )

        return branch

    def validate_company(self, company):
        user_company = self.get_user_company()

        if user_company is not None and company != user_company:
            raise serializers.ValidationError(
                "You cannot assign a product to another company."
            )

        return company

    # ------------------------------------------------------
    # CREATED BY NAME
    # ------------------------------------------------------

    def get_created_by_name(self, obj):
        if not obj.created_by:
            return "-"

        return (
            getattr(obj.created_by, "full_name", None)
            or getattr(obj.created_by, "name", None)
            or getattr(obj.created_by, "username", None)
            or str(obj.created_by)
        )

    # ------------------------------------------------------
    # CURRENT STOCK
    # ------------------------------------------------------

    def get_current_stock(self, obj):
        stocks = Stock.objects.filter(product=obj)
        branch = self.resolve_branch()

        if branch is not None:
            stocks = stocks.filter(branch=branch)

        return stocks.aggregate(
            total=Sum("quantity")
        )["total"] or 0

    # ------------------------------------------------------
    # CREATE PRODUCT
    # ------------------------------------------------------

    @transaction.atomic
    def create(self, validated_data):
        stock_quantity = validated_data.pop("stock", 0)
        branch = self.resolve_branch(validated_data)

        # Remove branch because Product has no branch field.
        validated_data.pop("branch", None)

        company = self.get_user_company()
        request = self.get_request()

        # Company ownership comes from the authenticated user
        # when the user model provides a company relationship.
        if company is not None:
            validated_data["company"] = company

        if request and request.user.is_authenticated:
            validated_data["created_by"] = request.user

        if stock_quantity > 0 and branch is None:
            raise serializers.ValidationError({
                "branch": (
                    "Select a branch before entering initial stock."
                )
            })

        product = Product.objects.create(**validated_data)

        # Only create inventory when a branch is known.
        if branch is not None:
            Stock.objects.update_or_create(
                product=product,
                branch=branch,
                defaults={"quantity": stock_quantity},
            )

        return product

    # ------------------------------------------------------
    # UPDATE PRODUCT
    # ------------------------------------------------------

    @transaction.atomic
    def update(self, instance, validated_data):
        stock_quantity = validated_data.pop("stock", None)
        branch = self.resolve_branch(validated_data)

        # Branch is an inventory input, not a Product field.
        validated_data.pop("branch", None)

        company = self.get_user_company()

        # Prevent a user's product from being reassigned to
        # another company through the update request.
        if company is not None:
            validated_data["company"] = company

        instance = super().update(instance, validated_data)

        # Do not touch stock unless stock was submitted.
        if stock_quantity is not None:
            if branch is None:
                raise serializers.ValidationError({
                    "branch": (
                        "Select a branch when updating stock."
                    )
                })

            Stock.objects.update_or_create(
                product=instance,
                branch=branch,
                defaults={"quantity": stock_quantity},
            )

        return instance

