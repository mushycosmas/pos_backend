from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Return(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_COMPLETED = "completed"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_REJECTED, "Rejected"),
    ]

    REFUND_CASH = "cash"
    REFUND_MOBILE = "mobile_money"
    REFUND_BANK = "bank"
    REFUND_STORE_CREDIT = "store_credit"

    REFUND_METHOD_CHOICES = [
        (REFUND_CASH, "Cash"),
        (REFUND_MOBILE, "Mobile Money"),
        (REFUND_BANK, "Bank"),
        (REFUND_STORE_CREDIT, "Store Credit"),
    ]

    REASON_WRONG_ITEM = "wrong_item"
    REASON_DAMAGED = "damaged"
    REASON_DEFECTIVE = "defective"
    REASON_CHANGE_MIND = "customer_change_mind"
    REASON_WRONG_QUANTITY = "wrong_quantity"
    REASON_EXPIRED = "expired"
    REASON_OTHER = "other"

    REASON_CHOICES = [
        (REASON_WRONG_ITEM, "Wrong Item"),
        (REASON_DAMAGED, "Damaged"),
        (REASON_DEFECTIVE, "Defective"),
        (REASON_CHANGE_MIND, "Customer Changed Mind"),
        (REASON_WRONG_QUANTITY, "Wrong Quantity"),
        (REASON_EXPIRED, "Expired"),
        (REASON_OTHER, "Other"),
    ]

    return_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
    )

    sale = models.ForeignKey(
        "sales.Sale",
        on_delete=models.PROTECT,
        related_name="returns",
    )

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="returns",
    )

    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.PROTECT,
        related_name="returns",
    )

    reason = models.CharField(
        max_length=50,
        choices=REASON_CHOICES,
    )

    notes = models.TextField(
        blank=True,
        default="",
    )

    refund_method = models.CharField(
        max_length=30,
        choices=REFUND_METHOD_CHOICES,
    )

    refund_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00"))
        ],
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_returns",
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_returns",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.return_number

    def save(self, *args, **kwargs):
        if not self.return_number:
            last_return = (
                Return.objects
                .filter(return_number__startswith="RET-")
                .order_by("-id")
                .first()
            )

            if last_return:
                try:
                    last_number = int(
                        last_return.return_number.replace(
                            "RET-",
                            "",
                        )
                    )
                    next_number = last_number + 1
                except ValueError:
                    next_number = Return.objects.count() + 1
            else:
                next_number = 1

            self.return_number = (
                f"RET-{next_number:06d}"
            )

        super().save(*args, **kwargs)


class ReturnItem(models.Model):

    return_record = models.ForeignKey(
        Return,
        on_delete=models.CASCADE,
        related_name="items",
    )

    sale_item = models.ForeignKey(
        "sales.SaleItem",
        on_delete=models.PROTECT,
        related_name="return_items",
    )

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="return_items",
    )

    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=3,
        validators=[
            MinValueValidator(Decimal("0.001"))
        ],
    )

    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):
        self.subtotal = (
            self.quantity * self.unit_price
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.product} - "
            f"{self.quantity}"
        )