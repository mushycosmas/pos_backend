
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from .models import Category, Brand, Product
from .serializers import (
    CategorySerializer,
    BrandSerializer,
    ProductSerializer,
)


# ==========================================================
# CATEGORY VIEWSET
# ==========================================================

class CategoryViewSet(ModelViewSet):
    """
    Manage product categories.
    """

    queryset = Category.objects.select_related(
        "parent"
    ).all()

    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


# ==========================================================
# BRAND VIEWSET
# ==========================================================

class BrandViewSet(ModelViewSet):
    """
    Manage product brands.
    """

    queryset = Brand.objects.all()

    serializer_class = BrandSerializer
    permission_classes = [AllowAny]


# ==========================================================
# PRODUCT VIEWSET
# ==========================================================

class ProductViewSet(ModelViewSet):
    """
    Manage company products and branch-specific assignments.

    Product details belong to a company.
    Stock records determine which products are available
    in the currently selected branch.

    Supported requests:
        GET /api/v1/products/?branch=1
        GET /api/v1/products/?branch_id=1

    Behavior:
        - Requires a valid branch ID for product listing.
        - Filters products by the authenticated user's company
          when that user has an associated company.
        - Returns products assigned to the selected branch
          through their Stock records.
        - Passes the selected branch to ProductSerializer.
        - Supports product creation with company and creator
          assignment for authenticated users.
    """

    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    # ------------------------------------------------------
    # BRANCH HELPER
    # ------------------------------------------------------

    def get_branch_id(self):
        """
        Read and validate the selected branch ID.

        Accepts either:
            ?branch=1
            ?branch_id=1
        """

        value = (
            self.request.query_params.get("branch")
            or self.request.query_params.get("branch_id")
        )

        if value is None:
            return None

        try:
            branch_id = int(value)

            if branch_id <= 0:
                return None

            return branch_id

        except (TypeError, ValueError):
            return None

    # ------------------------------------------------------
    # QUERYSET
    # ------------------------------------------------------

    def get_queryset(self):
        """
        Return products assigned to the selected branch.

        Products without a Stock record for that branch
        are excluded from the listing.
        """

        queryset = Product.objects.select_related(
            "category",
            "brand",
            "supplier",
            "company",
            "created_by",
        )

        # --------------------------------------------------
        # FILTER BY COMPANY
        # --------------------------------------------------

        user = self.request.user

        if user.is_authenticated:
            company = getattr(user, "company", None)

            if company is not None:
                queryset = queryset.filter(
                    company=company
                )

        # --------------------------------------------------
        # REQUIRE A VALID BRANCH
        # --------------------------------------------------

        branch_id = self.get_branch_id()

        if branch_id is None:
            return queryset.none()

        # --------------------------------------------------
        # FILTER BY SELECTED BRANCH
        # --------------------------------------------------

        queryset = queryset.filter(
            stocks__branch_id=branch_id
        ).distinct()

        return queryset

    # ------------------------------------------------------
    # SERIALIZER CONTEXT
    # ------------------------------------------------------

    def get_serializer_context(self):
        """
        Pass the selected branch to ProductSerializer.

        The serializer can use current_branch to calculate
        stock quantities for the selected branch.
        """

        context = super().get_serializer_context()

        branch_id = self.get_branch_id()

        if branch_id is not None:
            context["current_branch"] = branch_id

        return context

    # ------------------------------------------------------
    # CREATE PRODUCT
    # ------------------------------------------------------

    def perform_create(self, serializer):
        """
        Save the product with its creator and company
        when the authenticated user has those attributes.

        Branch-specific inventory assignment should be handled
        by the serializer or a dedicated inventory workflow.
        """

        user = self.request.user
        save_kwargs = {}

        if user.is_authenticated:
            save_kwargs["created_by"] = user

            company = getattr(user, "company", None)

            if company is not None:
                save_kwargs["company"] = company

        serializer.save(**save_kwargs)
