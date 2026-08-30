from django.shortcuts import render

# Create your views here.
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny

from .models import (
    ExpenseCategory,
    Expense,
    RecurringExpense,
    ExpenseBudget,
    ExpenseAttachment
)

from .serializers import (
    ExpenseCategorySerializer,
    ExpenseSerializer,
    RecurringExpenseSerializer,
    ExpenseBudgetSerializer,
    ExpenseAttachmentSerializer
)



class ExpenseCategoryViewSet(ModelViewSet):

    queryset = ExpenseCategory.objects.all()

    serializer_class = ExpenseCategorySerializer

    permission_classes = [
        AllowAny
    ]



class ExpenseViewSet(ModelViewSet):

    queryset = Expense.objects.select_related(
        'company',
        'branch',
        'category'
    )

    serializer_class = ExpenseSerializer

    permission_classes = [
        AllowAny
    ]



class RecurringExpenseViewSet(ModelViewSet):

    queryset = RecurringExpense.objects.all()

    serializer_class = RecurringExpenseSerializer

    permission_classes = [
        AllowAny
    ]



class ExpenseBudgetViewSet(ModelViewSet):

    queryset = ExpenseBudget.objects.all()

    serializer_class = ExpenseBudgetSerializer

    permission_classes = [
        AllowAny
    ]



class ExpenseAttachmentViewSet(ModelViewSet):

    queryset = ExpenseAttachment.objects.all()

    serializer_class = ExpenseAttachmentSerializer

    permission_classes = [
        AllowAny
    ]