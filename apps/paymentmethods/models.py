from django.db import models


class PaymentMethod(models.Model):
    PAYMENT_TYPES = (
        ("cash", "Cash"),
        ("mobile_money", "Mobile Money"),
        ("card", "Card"),
        ("bank", "Bank"),
        ("credit", "Credit"),
        ("other", "Other"),
    )

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    code = models.CharField(
        max_length=50,
        unique=True,
    )

    payment_type = models.CharField(
        max_length=30,
        choices=PAYMENT_TYPES,
    )

    provider = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    allow_change = models.BooleanField(
        default=False,
    )

    transaction_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    display_order = models.PositiveIntegerField(
        default=0,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["display_order", "name"]

        indexes = [
            models.Index(
                fields=["is_active"]
            ),
            models.Index(
                fields=["payment_type"]
            ),
        ]

    def __str__(self):
        return self.name