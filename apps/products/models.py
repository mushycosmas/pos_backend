from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.companies.models import Company
from apps.suppliers.models import Supplier


# ==========================================================
# CATEGORY
# ==========================================================

class Category(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        blank=True
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children"
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "categories"
        ordering = ["name"]


# ==========================================================
# BRAND
# ==========================================================

class Brand(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "brands"
        ordering = ["name"]


# ==========================================================
# PRODUCT
# ==========================================================

class Product(models.Model):

    # ------------------------------------------------------
    # BASIC INFORMATION
    # ------------------------------------------------------

    name = models.CharField(
        max_length=200
    )

    sku = models.CharField(
        max_length=50,
        unique=True
    )

    barcode = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True
    )

    # ------------------------------------------------------
    # CATEGORY
    # ------------------------------------------------------

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )

    # ------------------------------------------------------
    # BRAND
    # ------------------------------------------------------

    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )

    # ------------------------------------------------------
    # SUPPLIER
    # ------------------------------------------------------

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )

    # ------------------------------------------------------
    # PRICING
    # ------------------------------------------------------

    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(0)
        ]
    )

    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(0)
        ]
    )

    wholesale_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0)
        ]
    )

    # ------------------------------------------------------
    # TAX
    # ------------------------------------------------------

    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )

    # ------------------------------------------------------
    # DESCRIPTION
    # ------------------------------------------------------

    description = models.TextField(
        blank=True
    )

    # ------------------------------------------------------
    # IMAGE
    # ------------------------------------------------------

    image = models.ImageField(
        upload_to="products/",
        null=True,
        blank=True
    )

    # ------------------------------------------------------
    # INVENTORY
    # ------------------------------------------------------

    minimum_stock = models.PositiveIntegerField(
        default=5
    )

    # ------------------------------------------------------
    # STATUS
    # ------------------------------------------------------

    is_active = models.BooleanField(
        default=True
    )

    is_kitchen = models.BooleanField(
        default=False
    )

    # ------------------------------------------------------
    # COMPANY
    # ------------------------------------------------------

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="products"
    )

    # ------------------------------------------------------
    # TIMESTAMPS
    # ------------------------------------------------------

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # ======================================================
    # METHODS
    # ======================================================

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def get_current_stock(self):

        from apps.inventory.models import Stock

        stock = Stock.objects.filter(
            product=self
        ).first()

        return stock.quantity if stock else 0

    # ======================================================
    # META
    # ======================================================

    class Meta:
        db_table = "products"
        ordering = ["name"]