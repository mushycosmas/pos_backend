from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.branches.models import Branch
from .models import Customer
from .serializers import CustomerSerializer


class CustomerViewSet(ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def get_selected_branch(self):
        """
        Read the selected branch from X-Branch-ID and verify
        that it belongs to the user's company.
        """
        branch_id = self.request.headers.get("X-Branch-ID")

        if not branch_id:
            raise ValidationError({
                "branch": "X-Branch-ID header is required."
            })

        try:
            branch_id = int(branch_id)
        except (TypeError, ValueError):
            raise ValidationError({
                "branch": "Invalid branch ID."
            })

        user_branch = getattr(self.request.user, "branch", None)

        if not user_branch or not user_branch.company_id:
            raise PermissionDenied(
                "Your account must be assigned to a branch "
                "belonging to a company."
            )

        return get_object_or_404(
            Branch.objects.filter(
                company_id=user_branch.company_id,
                is_active=True,
            ),
            pk=branch_id,
        )

    def get_queryset(self):
        branch = self.get_selected_branch()

        return (
            Customer.objects.select_related("company", "branch")
            .filter(
                company_id=branch.company_id,
                branch_id=branch.id,
            )
            .order_by("name")
        )

    def perform_create(self, serializer):
        branch = self.get_selected_branch()

        serializer.save(
            company_id=branch.company_id,
            branch=branch,
        )

    def perform_update(self, serializer):
        # The customer must already belong to the selected branch,
        # because get_queryset() enforces branch-level filtering.
        branch = self.get_selected_branch()

        serializer.save(
            company_id=branch.company_id,
            branch=branch,
        )

    @action(detail=True, methods=["get"], url_path="sales")
    def sales_history(self, request, pk=None):
        customer = self.get_object()

        sales = customer.sales.all().order_by("-created_at")

        data = [
            {
                "invoice": sale.invoice_number,
                "total": sale.total,
                "status": sale.status,
                "date": sale.created_at,
            }
            for sale in sales
        ]

        return Response(data, status=status.HTTP_200_OK)
