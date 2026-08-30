from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny

from .models import (
    Category,
    Brand,
    Product,
)

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
    API endpoint for managing product categories.

    Endpoints:
        GET     /categories/
        POST    /categories/
        GET     /categories/<id>/
        PUT     /categories/<id>/
        PATCH   /categories/<id>/
        DELETE  /categories/<id>/
    """

    queryset = (
        Category.objects
        .select_related("parent")
        .all()
    )

    serializer_class = CategorySerializer

    permission_classes = [
        AllowAny
    ]


# ==========================================================
# BRAND VIEWSET
# ==========================================================

class BrandViewSet(ModelViewSet):
    """
    API endpoint for managing product brands.

    Endpoints:
        GET     /brands/
        POST    /brands/
        GET     /brands/<id>/
        PUT     /brands/<id>/
        PATCH   /brands/<id>/
        DELETE  /brands/<id>/
    """

    queryset = (
        Brand.objects
        .all()
    )

    serializer_class = BrandSerializer

    permission_classes = [
        AllowAny
    ]


# ==========================================================
# PRODUCT VIEWSET
# ==========================================================

class ProductViewSet(ModelViewSet):
    """
    API endpoint for managing products.

    Endpoints:
        GET     /products/
        POST    /products/
        GET     /products/<id>/
        PUT     /products/<id>/
        PATCH   /products/<id>/
        DELETE  /products/<id>/
    """

    queryset = (
        Product.objects
        .select_related(
            "category",
            "brand",
            "company",
        )
        .all()
    )

    serializer_class = ProductSerializer

    permission_classes = [
        AllowAny
    ]