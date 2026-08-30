from rest_framework.routers import DefaultRouter

from .views import (
    ExpenseCategoryViewSet,
    ExpenseViewSet,
    RecurringExpenseViewSet,
    ExpenseBudgetViewSet,
    ExpenseAttachmentViewSet
)


router = DefaultRouter()


router.register(
    'expense-categories',
    ExpenseCategoryViewSet
)


router.register(
    'expenses',
    ExpenseViewSet
)


router.register(
    'recurring-expenses',
    RecurringExpenseViewSet
)


router.register(
    'expense-budgets',
    ExpenseBudgetViewSet
)


router.register(
    'expense-attachments',
    ExpenseAttachmentViewSet
)



urlpatterns = router.urls