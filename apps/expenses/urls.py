from rest_framework.routers import DefaultRouter

from .views import (
    ExpenseCategoryViewSet,
    ExpenseViewSet,
    RecurringExpenseViewSet,
    ExpenseBudgetViewSet,
    ExpenseAttachmentViewSet,
)


router = DefaultRouter()

router.register(
    r"expense-categories",
    ExpenseCategoryViewSet,
    basename="expense-category",
)

router.register(
    r"expenses",
    ExpenseViewSet,
    basename="expense",
)

router.register(
    r"recurring-expenses",
    RecurringExpenseViewSet,
    basename="recurring-expense",
)

router.register(
    r"expense-budgets",
    ExpenseBudgetViewSet,
    basename="expense-budget",
)

router.register(
    r"expense-attachments",
    ExpenseAttachmentViewSet,
    basename="expense-attachment",
)


urlpatterns = router.urls