from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Branch
from .serializers import BranchSerializer


class BranchViewSet(ModelViewSet):
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]

    def get_user_company(self):
        user = self.request.user

        user_branch = getattr(user, "branch", None)

        if not user_branch:
            raise ValidationError({
                "detail": "Your user is not assigned to a branch."
            })

        company = getattr(user_branch, "company", None)

        if not company:
            raise ValidationError({
                "detail": "Your branch is not assigned to a company."
            })

        if not company.is_active:
            raise ValidationError({
                "detail": "Your company is inactive."
            })

        return company

    def get_queryset(self):
        company = self.get_user_company()

        return (
            Branch.objects
            .filter(company=company)
            .select_related("company")
            .order_by("name")
        )

    def perform_create(self, serializer):
        company = self.get_user_company()

        serializer.save(
            company=company,
            is_main=False,
        )

    def perform_update(self, serializer):
        company = self.get_user_company()

        branch = self.get_object()

        if branch.company_id != company.id:
            raise ValidationError({
                "detail": "You are not allowed to modify this branch."
            })

        if branch.is_main:
            serializer.save(
                company=company,
                is_main=True,
            )
        else:
            serializer.save(
                company=company,
                is_main=False,
            )

    def destroy(self, request, *args, **kwargs):
        branch = self.get_object()

        if branch.is_main:
            return Response(
                {
                    "detail": "The Main Branch cannot be deleted."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response = super().destroy(request, *args, **kwargs)

        return response