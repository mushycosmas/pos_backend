from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from django.db.models import Q

from .models import Supplier
from .serializers import SupplierSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing suppliers.

    Supported methods:
    GET     /suppliers/
    POST    /suppliers/
    GET     /suppliers/{id}/
    PUT     /suppliers/{id}/
    PATCH   /suppliers/{id}/
    DELETE  /suppliers/{id}/
    """

    serializer_class = SupplierSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Supplier.objects.all().order_by("name")

        is_active = self.request.query_params.get("is_active")
        search = self.request.query_params.get("search")

        # Filter by active status
        if is_active is not None:
            if is_active.lower() == "true":
                queryset = queryset.filter(is_active=True)

            elif is_active.lower() == "false":
                queryset = queryset.filter(is_active=False)

        # Search
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(phone__icontains=search)
                | Q(email__icontains=search)
                | Q(address__icontains=search)
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()