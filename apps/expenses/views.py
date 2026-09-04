from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import (
    ExpenseCategory,
    Expense,
    RecurringExpense,
    ExpenseBudget,
    ExpenseAttachment,
)

from .serializers import (
    ExpenseCategorySerializer,
    ExpenseSerializer,
    RecurringExpenseSerializer,
    ExpenseBudgetSerializer,
    ExpenseAttachmentSerializer,
)


# =========================================================
# EXPENSE CATEGORY
# =========================================================

class ExpenseCategoryViewSet(ModelViewSet):

    queryset = ExpenseCategory.objects.select_related(
        "company",
        "created_by",
        "updated_by",
    )

    serializer_class = ExpenseCategorySerializer

    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(
            updated_by=self.request.user,
        )


# =========================================================
# EXPENSE
# =========================================================

class ExpenseViewSet(ModelViewSet):

    queryset = Expense.objects.select_related(
        "company",
        "branch",
        "category",
        "created_by",
        "updated_by",
        "approved_by",
        "rejected_by",
    )

    serializer_class = ExpenseSerializer

    permission_classes = [IsAuthenticated]

    # =====================================================
    # CREATE
    # =====================================================

    def perform_create(self, serializer):

        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    # =====================================================
    # UPDATE
    # =====================================================

    def perform_update(self, serializer):

        serializer.save(
            updated_by=self.request.user,
        )

    # =====================================================
    # APPROVE EXPENSE
    # POST /expenses/{id}/approve/
    # =====================================================

    @action(
        detail=True,
        methods=["post"],
        url_path="approve",
    )
    def approve(self, request, pk=None):

        expense = self.get_object()

        # ---------------------------------------------
        # Already approved
        # ---------------------------------------------

        if expense.is_approved:

            return Response(
                {
                    "detail": "This expense is already approved."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # Already rejected
        # ---------------------------------------------

        if expense.is_rejected:

            return Response(
                {
                    "detail": (
                        "This expense has already been rejected "
                        "and cannot be approved."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # Approve
        # ---------------------------------------------

        expense.is_approved = True

        expense.approved_by = request.user

        expense.approved_at = timezone.now()

        expense.updated_by = request.user

        expense.save()

        return Response(
            self.get_serializer(expense).data,
            status=status.HTTP_200_OK,
        )

    # =====================================================
    # REJECT EXPENSE
    # POST /expenses/{id}/reject/
    # =====================================================

    @action(
        detail=True,
        methods=["post"],
        url_path="reject",
    )
    def reject(self, request, pk=None):

        expense = self.get_object()

        # ---------------------------------------------
        # Already approved
        # ---------------------------------------------

        if expense.is_approved:

            return Response(
                {
                    "detail": (
                        "This expense has already been approved "
                        "and cannot be rejected."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # Already rejected
        # ---------------------------------------------

        if expense.is_rejected:

            return Response(
                {
                    "detail": "This expense is already rejected."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # Get rejection reason
        # ---------------------------------------------

        reason = request.data.get(
            "rejection_reason",
            "",
        )

        reason = str(reason).strip()

        if not reason:

            return Response(
                {
                    "detail": "Rejection reason is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # Reject
        # ---------------------------------------------

        expense.is_approved = False

        expense.is_rejected = True

        expense.rejection_reason = reason

        expense.rejected_by = request.user

        expense.rejected_at = timezone.now()

        expense.updated_by = request.user

        expense.save()

        return Response(
            self.get_serializer(expense).data,
            status=status.HTTP_200_OK,
        )


# =========================================================
# RECURRING EXPENSE
# =========================================================

class RecurringExpenseViewSet(ModelViewSet):

    queryset = RecurringExpense.objects.select_related(
        "category",
        "branch",
        "company",
        "created_by",
        "updated_by",
    )

    serializer_class = RecurringExpenseSerializer

    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):

        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):

        serializer.save(
            updated_by=self.request.user,
        )


# =========================================================
# EXPENSE BUDGET
# =========================================================

class ExpenseBudgetViewSet(ModelViewSet):

    queryset = ExpenseBudget.objects.select_related(
        "category",
        "branch",
        "company",
        "created_by",
        "updated_by",
    )

    serializer_class = ExpenseBudgetSerializer

    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):

        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):

        serializer.save(
            updated_by=self.request.user,
        )


# =========================================================
# EXPENSE ATTACHMENT
# =========================================================

class ExpenseAttachmentViewSet(ModelViewSet):

    queryset = ExpenseAttachment.objects.select_related(
        "expense",
        "uploaded_by",
        "updated_by",
    )

    serializer_class = ExpenseAttachmentSerializer

    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):

        serializer.save(
            uploaded_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):

        serializer.save(
            updated_by=self.request.user,
        )