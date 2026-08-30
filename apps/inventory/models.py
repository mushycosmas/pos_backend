from django.db import models
from django.core.validators import MinValueValidator

from apps.products.models import Product
from apps.branches.models import Branch


class Stock(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="stocks"
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="stocks"
    )

    quantity = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0)
        ]
    )

    reserved_quantity = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0)
        ]
    )

    min_quantity = models.IntegerField(
        default=5,
        validators=[
            MinValueValidator(0)
        ]
    )

    max_quantity = models.IntegerField(
        default=1000,
        validators=[
            MinValueValidator(0)
        ]
    )

    last_updated = models.DateTimeField(
        auto_now=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "stocks"

        constraints = [
            models.UniqueConstraint(
                fields=["product", "branch"],
                name="unique_product_branch_stock"
            )
        ]

    def __str__(self):
        return (
            f"{self.product.name} - "
            f"{self.branch.name}: "
            f"{self.quantity}"
        )


class StockMovement(models.Model):

    MOVEMENT_TYPES = (
        ("IN", "Stock In"),
        ("OUT", "Stock Out"),
        ("TRANSFER", "Transfer"),
        ("ADJUSTMENT", "Adjustment"),
        ("SALE", "Sale"),
        ("PURCHASE", "Purchase"),
        ("RETURN", "Return"),
        ("WASTE", "Waste"),
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="stock_movements"
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="stock_movements"
    )

    quantity = models.IntegerField()

    previous_quantity = models.IntegerField()

    new_quantity = models.IntegerField()

    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPES
    )

    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    notes = models.TextField(
        blank=True
    )

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "stock_movements"

        ordering = [
            "-created_at"
        ]

    def __str__(self):
        return (
            f"{self.product.name} - "
            f"{self.movement_type} - "
            f"{self.quantity}"
        )