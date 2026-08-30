from rest_framework import serializers

from .models import (
    ExpenseCategory,
    Expense,
    RecurringExpense,
    ExpenseBudget,
    ExpenseAttachment
)



class ExpenseCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ExpenseCategory

        fields = [
            'id',
            'name',
            'description',
            'company',
            'is_active',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'created_at',
            'updated_at'
        ]



class ExpenseSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(
        source='category.name',
        read_only=True
    )

    branch_name = serializers.CharField(
        source='branch.name',
        read_only=True
    )

    company_name = serializers.CharField(
        source='company.name',
        read_only=True
    )

    expense_type_name = serializers.CharField(
        source='get_expense_type_display',
        read_only=True
    )


    class Meta:

        model = Expense

        fields = [
            'id',

            'title',
            'description',

            'category',
            'category_name',

            'expense_type',
            'expense_type_name',

            'amount',
            'tax',
            'total',

            'expense_date',
            'due_date',

            'branch',
            'branch_name',

            'company',
            'company_name',

            'payment_status',
            'payment_method',
            'payment_date',

            'receipt',
            'invoice_number',
            'reference',

            'is_approved',
            'approved_by',
            'approved_at',

            'is_rejected',
            'rejection_reason',

            'created_by',

            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'total',
            'created_at',
            'updated_at'
        ]



class RecurringExpenseSerializer(serializers.ModelSerializer):

    class Meta:

        model = RecurringExpense

        fields = '__all__'

        read_only_fields = [
            'created_at',
            'updated_at'
        ]



class ExpenseBudgetSerializer(serializers.ModelSerializer):

    variance = serializers.SerializerMethodField()


    class Meta:

        model = ExpenseBudget

        fields = [
            'id',
            'category',
            'branch',
            'company',
            'period',
            'year',
            'month',
            'quarter',
            'budgeted_amount',
            'actual_amount',
            'variance',
            'notes',
            'created_by',
            'created_at',
            'updated_at',
        ]


    def get_variance(self,obj):

        return obj.variance()



class ExpenseAttachmentSerializer(serializers.ModelSerializer):

    class Meta:

        model = ExpenseAttachment

        fields = '__all__'