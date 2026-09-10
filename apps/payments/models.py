from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator

from apps.sales.models import Sale
from apps.companies.models import Company
from apps.branches.models import Branch
from apps.paymentmethods.models import PaymentMethod


class Payment(models.Model):
    """Payment transactions"""

    PAYMENT_STATUS = (
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
        ("partially_refunded", "Partially Refunded"),
    )

    PAYMENT_DIRECTION = (
        ("incoming", "Incoming"),
        ("outgoing", "Outgoing"),
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="payments",
        null=True,
        blank=True,
    )

    purchase = models.ForeignKey(
        "purchases.Purchase",
        on_delete=models.CASCADE,
        related_name="payments",
        null=True,
        blank=True,
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # =====================================================
    # PAYMENT METHOD
    # =====================================================

    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        related_name="payments",
        null=True,
        blank=True,
    )

    # =====================================================
    # PAYMENT DETAILS
    # =====================================================

    direction = models.CharField(
        max_length=20,
        choices=PAYMENT_DIRECTION,
        default="incoming",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    currency = models.CharField(
        max_length=3,
        default="TZS",
    )

    # =====================================================
    # REFERENCE DETAILS
    # =====================================================

    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    # =====================================================
    # PAYMENT GATEWAY
    # =====================================================

    gateway = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )

    gateway_response = models.JSONField(
        default=dict,
        blank=True,
    )

    # =====================================================
    # PAYMENT STATUS
    # =====================================================

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default="pending",
    )

    # =====================================================
    # DATES
    # =====================================================

    payment_date = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    # =====================================================
    # ADDITIONAL INFORMATION
    # =====================================================

    notes = models.TextField(blank=True)

    processed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_payments",
    )

    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_payments",
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # =====================================================
    # METHODS
    # =====================================================

    def __str__(self):
        payment_method_name = (
            self.payment_method.name
            if self.payment_method
            else "No Payment Method"
        )
        return (
            f"{payment_method_name} - "
            f"{self.amount} - "
            f"{self.status}"
        )

    def save(self, *args, **kwargs):
        """
        Automatically set branch and company
        from Sale or Purchase when available.
        """
        # Set branch from sale or purchase
        if not self.branch:
            if self.sale:
                self.branch = self.sale.branch
            elif self.purchase:
                self.branch = self.purchase.branch

        # Set company from sale or purchase
        if not self.company:
            if self.sale:
                self.company = self.sale.company
            elif self.purchase:
                self.company = self.purchase.company

        super().save(*args, **kwargs)

    class Meta:
        db_table = "payments"
        ordering = ["-payment_date"]
        indexes = [
            models.Index(fields=["transaction_id"]),
            models.Index(fields=["reference"]),
            models.Index(fields=["status"]),
            # NOTE: FK fields already create an index in Django.
            # Keep this only if you frequently filter by this FK
            # in a way that benefits from an explicit composite index.
            models.Index(fields=["payment_method"]),
        ]


class PaymentGateway(models.Model):
    """Payment gateway configurations"""

    GATEWAY_TYPES = (
        ("mobile_money", "Mobile Money"),
        ("bank", "Bank"),
        ("card", "Card"),
        ("wallet", "Wallet"),
        ("other", "Other"),
    )

    # =====================================================
    # BASIC INFORMATION
    # =====================================================

    name = models.CharField(max_length=100)

    code = models.CharField(
        max_length=20,
        unique=True,
    )

    gateway_type = models.CharField(
        max_length=20,
        choices=GATEWAY_TYPES,
    )

    # =====================================================
    # API CONFIGURATION
    # =====================================================

    api_url = models.URLField()

    api_key = models.CharField(
        max_length=255,
        blank=True,
    )

    api_secret = models.CharField(
        max_length=255,
        blank=True,
    )

    merchant_id = models.CharField(
        max_length=100,
        blank=True,
    )

    callback_url = models.URLField(blank=True)

    # =====================================================
    # SETTINGS
    # =====================================================

    is_active = models.BooleanField(default=True)

    is_test_mode = models.BooleanField(default=False)

    test_api_url = models.URLField(blank=True)

    test_api_key = models.CharField(
        max_length=255,
        blank=True,
    )

    test_api_secret = models.CharField(
        max_length=255,
        blank=True,
    )

    test_merchant_id = models.CharField(
        max_length=100,
        blank=True,
    )

    # =====================================================
    # SUPPORTED PAYMENT METHODS
    # =====================================================

    supported_methods = models.JSONField(
        default=list,
        blank=True,
    )

    # =====================================================
    # COMPANY
    # =====================================================

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    # =====================================================
    # DATES
    # =====================================================

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "payment_gateways"
        ordering = ["name"]


class PaymentTransactionLog(models.Model):
    """Log for payment transactions"""

    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="logs",
    )

    action = models.CharField(max_length=50)

    request_data = models.JSONField(
        default=dict,
        blank=True,
    )

    response_data = models.JSONField(
        default=dict,
        blank=True,
    )

    status = models.CharField(max_length=20)

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.payment_id} - {self.action} - {self.status}"

    class Meta:
        db_table = "payment_transaction_logs"
        ordering = ["-created_at"]


class PaymentBatch(models.Model):
    """Batch payments for payroll, suppliers, refunds, etc."""

    BATCH_STATUS = (
        ("draft", "Draft"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("failed", "Failed"),
    )

    # =====================================================
    # BASIC INFORMATION
    # =====================================================

    name = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    batch_type = models.CharField(max_length=50)

    # =====================================================
    # AMOUNTS
    # =====================================================

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    total_items = models.IntegerField(default=0)

    # =====================================================
    # STATUS
    # =====================================================

    status = models.CharField(
        max_length=20,
        choices=BATCH_STATUS,
        default="draft",
    )

    # =====================================================
    # COMPANY / BRANCH
    # =====================================================

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # =====================================================
    # USERS
    # =====================================================

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_batches",
    )

    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_batches",
    )

    # =====================================================
    # DATES
    # =====================================================

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.name} - {self.total_amount}"

    class Meta:
        db_table = "payment_batches"
        ordering = ["-created_at"]