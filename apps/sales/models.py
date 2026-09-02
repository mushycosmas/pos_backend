
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


# =========================================================
# SALE
# =========================================================

class Sale(models.Model):

    PAYMENT_METHODS = (
        ("CASH", "Cash"),
        ("CARD", "Card"),
        ("M-PESA", "M-PESA"),
        ("BANK_TRANSFER", "Bank Transfer"),
    )

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
        ("REFUNDED", "Refunded"),
    )

    # =====================================================
    # BRANCH
    # =====================================================

    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sales",
    )

    # =====================================================
    # CUSTOMER
    # =====================================================

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales",
    )

    # =====================================================
    # INVOICE
    # =====================================================

    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
    )

    # =====================================================
    # CUSTOMER SNAPSHOT
    #
    # Keeps customer information at the time of sale.
    # Useful even if the customer is later changed/deleted.
    # =====================================================

    customer_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    customer_phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
    )

    # =====================================================
    # SALE AMOUNTS
    # =====================================================

    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00"))
        ],
    )

    discount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00"))
        ],
    )

    # VAT percentage
    # Example: 18.00 = 18%
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("18.00"),
        validators=[
            MinValueValidator(Decimal("0.00"))
        ],
    )

    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00"))
        ],
    )

    total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00"))
        ],
    )

    # =====================================================
    # PAYMENT
    # =====================================================

    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHODS,
        default="CASH",
    )

    amount_paid = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00"))
        ],
    )

    change = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00"))
        ],
    )

    # =====================================================
    # STATUS
    # =====================================================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="COMPLETED",
    )

    # =====================================================
    # NOTES
    # =====================================================

    notes = models.TextField(
        blank=True,
        default="",
    )

    # =====================================================
    # TIMESTAMPS
    #
    # default=timezone.now is migration-friendly because
    # existing records can receive a timestamp.
    # =====================================================

    created_at = models.DateTimeField(
        default=timezone.now,
    )

    updated_at = models.DateTimeField(
        default=timezone.now,
    )

    # =====================================================
    # STRING REPRESENTATION
    # =====================================================

    def __str__(self):
        return (
            f"{self.invoice_number or f'Sale #{self.id}'} "
            f"- {self.total}"
        )

    # =====================================================
    # SAVE
    # =====================================================

    def save(self, *args, **kwargs):

        is_new = self.pk is None

        # Automatically create invoice number after ID exists
        if is_new and not self.invoice_number:

            super().save(*args, **kwargs)

            self.invoice_number = f"INV-{self.id:06d}"

            super().save(
                update_fields=["invoice_number"]
            )

            return

        # Update timestamp
        self.updated_at = timezone.now()

        super().save(*args, **kwargs)


# =========================================================
# SALE ITEM
# =========================================================

class SaleItem(models.Model):

    # =====================================================
    # SALE
    # =====================================================

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="items",
    )

    # =====================================================
    # PRODUCT
    # =====================================================

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="sale_items",
    )

    # =====================================================
    # QUANTITY
    # =====================================================

    quantity = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1)
        ],
    )

    # =====================================================
    # UNIT PRICE
    # =====================================================

    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00"))
        ],
    )

    # =====================================================
    # ITEM DISCOUNT
    # =====================================================

    discount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00"))
        ],
    )

    # =====================================================
    # ITEM TAX
    # =====================================================

    tax = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00"))
        ],
    )

    # =====================================================
    # ITEM TOTAL
    # =====================================================

    total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00"))
        ],
    )

    # =====================================================
    # TIMESTAMP
    #
    # Using default instead of auto_now_add makes migration
    # easier when SaleItem already contains records.
    # =====================================================

    created_at = models.DateTimeField(
        default=timezone.now,
    )

    # =====================================================
    # SAVE
    # =====================================================

    def save(self, *args, **kwargs):

        # Automatically calculate item total
        subtotal = (
            Decimal(self.quantity)
            * self.unit_price
        )

        subtotal -= self.discount

        subtotal += self.tax

        if subtotal < Decimal("0.00"):
            subtotal = Decimal("0.00")

        self.total = subtotal

        super().save(*args, **kwargs)

    # =====================================================
    # STRING REPRESENTATION
    # =====================================================

    def __str__(self):
        return (
            f"{self.product.name} x {self.quantity}"
        )

