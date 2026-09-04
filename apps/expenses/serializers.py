from rest_framework import serializers

from .models import (
    ExpenseCategory,
    Expense,
    RecurringExpense,
    ExpenseBudget,
    ExpenseAttachment,
)


# ============================================================
# USER NAME HELPER
# ============================================================

def get_user_display_name(user):

    if not user:
        return None

    full_name = user.get_full_name()

    if full_name:
        return full_name

    if getattr(user, 'username', None):
        return user.username

    if getattr(user, 'email', None):
        return user.email

    return None


# ============================================================
# EXPENSE CATEGORY SERIALIZER
# ============================================================

class ExpenseCategorySerializer(
    serializers.ModelSerializer
):

    created_by_name = serializers.SerializerMethodField()

    updated_by_name = serializers.SerializerMethodField()

    class Meta:

        model = ExpenseCategory

        fields = [
            'id',

            'name',
            'description',

            'company',

            'is_active',

            'created_by',
            'created_by_name',

            'updated_by',
            'updated_by_name',

            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',

            'created_by',
            'created_by_name',

            'updated_by',
            'updated_by_name',

            'created_at',
            'updated_at',
        ]

    def get_created_by_name(self, obj):

        return get_user_display_name(
            obj.created_by
        )

    def get_updated_by_name(self, obj):

        return get_user_display_name(
            obj.updated_by
        )


# ============================================================
# EXPENSE SERIALIZER
# ============================================================

class ExpenseSerializer(
    serializers.ModelSerializer
):

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

    payment_status_name = serializers.CharField(
        source='get_payment_status_display',
        read_only=True
    )

    created_by_name = serializers.SerializerMethodField()

    updated_by_name = serializers.SerializerMethodField()

    approved_by_name = serializers.SerializerMethodField()

    rejected_by_name = serializers.SerializerMethodField()

    class Meta:

        model = Expense

        fields = [

            # ------------------------------------------------
            # BASIC
            # ------------------------------------------------

            'id',

            'title',
            'description',

            'category',
            'category_name',

            'expense_type',
            'expense_type_name',

            # ------------------------------------------------
            # FINANCIAL
            # ------------------------------------------------

            'amount',
            'tax',
            'total',

            # ------------------------------------------------
            # DATES
            # ------------------------------------------------

            'expense_date',
            'due_date',

            # ------------------------------------------------
            # LOCATION
            # ------------------------------------------------

            'branch',
            'branch_name',

            'company',
            'company_name',

            # ------------------------------------------------
            # PAYMENT
            # ------------------------------------------------

            'payment_status',
            'payment_status_name',

            'payment_method',
            'payment_date',

            # ------------------------------------------------
            # REFERENCES
            # ------------------------------------------------

            'receipt',
            'invoice_number',
            'reference',

            # ------------------------------------------------
            # APPROVAL
            # ------------------------------------------------

            'is_approved',

            'approved_by',
            'approved_by_name',

            'approved_at',

            # ------------------------------------------------
            # REJECTION
            # ------------------------------------------------

            'is_rejected',

            'rejection_reason',

            'rejected_by',
            'rejected_by_name',

            'rejected_at',

            # ------------------------------------------------
            # AUDIT
            # ------------------------------------------------

            'created_by',
            'created_by_name',

            'updated_by',
            'updated_by_name',

            # ------------------------------------------------
            # TIMESTAMPS
            # ------------------------------------------------

            'created_at',
            'updated_at',
        ]

        read_only_fields = [

            'id',

            'total',

            # Audit
            'created_by',
            'created_by_name',

            'updated_by',
            'updated_by_name',

            # Approval
            'approved_by',
            'approved_by_name',
            'approved_at',

            # Rejection
            'rejected_by',
            'rejected_by_name',
            'rejected_at',

            # Timestamps
            'created_at',
            'updated_at',
        ]

    # ========================================================
    # CREATED BY
    # ========================================================

    def get_created_by_name(self, obj):

        return get_user_display_name(
            obj.created_by
        )

    # ========================================================
    # UPDATED BY
    # ========================================================

    def get_updated_by_name(self, obj):

        return get_user_display_name(
            obj.updated_by
        )

    # ========================================================
    # APPROVED BY
    # ========================================================

    def get_approved_by_name(self, obj):

        return get_user_display_name(
            obj.approved_by
        )

    # ========================================================
    # REJECTED BY
    # ========================================================

    def get_rejected_by_name(self, obj):

        return get_user_display_name(
            obj.rejected_by
        )


# ============================================================
# RECURRING EXPENSE SERIALIZER
# ============================================================

class RecurringExpenseSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = RecurringExpense

        fields = '__all__'

        read_only_fields = [
            'total',

            'created_by',
            'updated_by',

            'created_at',
            'updated_at',
        ]


# ============================================================
# EXPENSE BUDGET SERIALIZER
# ============================================================

class ExpenseBudgetSerializer(
    serializers.ModelSerializer
):

    variance = serializers.SerializerMethodField()

    variance_percentage = serializers.SerializerMethodField()

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
            'variance_percentage',

            'notes',

            'created_by',
            'updated_by',

            'created_at',
            'updated_at',
        ]

        read_only_fields = [

            'id',

            'variance',
            'variance_percentage',

            'created_by',
            'updated_by',

            'created_at',
            'updated_at',
        ]

    def get_variance(self, obj):

        return obj.variance()

    def get_variance_percentage(self, obj):

        return obj.variance_percentage()


# ============================================================
# EXPENSE ATTACHMENT SERIALIZER
# ============================================================

class ExpenseAttachmentSerializer(
    serializers.ModelSerializer
):

    uploaded_by_name = serializers.SerializerMethodField()

    updated_by_name = serializers.SerializerMethodField()

    class Meta:

        model = ExpenseAttachment

        fields = [
            'id',

            'expense',

            'file',
            'filename',
            'file_size',
            'file_type',

            'uploaded_by',
            'uploaded_by_name',

            'updated_by',
            'updated_by_name',

            'uploaded_at',
            'updated_at',
        ]

        read_only_fields = [

            'id',

            'uploaded_by',
            'uploaded_by_name',

            'updated_by',
            'updated_by_name',

            'uploaded_at',
            'updated_at',
        ]

    def get_uploaded_by_name(self, obj):

        return get_user_display_name(
            obj.uploaded_by
        )

    def get_updated_by_name(self, obj):

        return get_user_display_name(
            obj.updated_by
        )