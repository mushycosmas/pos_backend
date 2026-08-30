from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.utils import timezone

from apps.products.models import Product
from apps.suppliers.models import Supplier
from apps.branches.models import Branch
from apps.companies.models import Company


class Purchase(models.Model):

    # ==========================================================
    # STATUS
    # ==========================================================

    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("ordered", "Ordered"),
        ("received", "Received"),
        ("partially_received", "Partially Received"),
        ("cancelled", "Cancelled"),
    )

    # ==========================================================
    # PAYMENT STATUS
    # ==========================================================

    PAYMENT_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("partial", "Partial"),
    )

    # ==========================================================
    # PURCHASE INFORMATION
    # ==========================================================

    purchase_number = models.CharField(
        max_length=50,
        unique=True,
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="purchases",
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="purchases",
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="purchases",
    )

    # ==========================================================
    # DATES
    # ==========================================================

    order_date = models.DateTimeField(
        auto_now_add=True,
    )

    expected_delivery_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    received_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    # ==========================================================
    # FINANCIAL INFORMATION
    # ==========================================================

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    shipping_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    # ==========================================================
    # STATUS
    # ==========================================================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending",
    )

    # ==========================================================
    # OTHER
    # ==========================================================

    notes = models.TextField(
        blank=True,
        default="",
    )

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_purchases",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    # ==========================================================
    # STRING
    # ==========================================================

    def __str__(self):
        return f"Purchase {self.purchase_number}"

    # ==========================================================
    # AUTO PURCHASE NUMBER
    # ==========================================================

    def save(self, *args, **kwargs):

        if not self.purchase_number:

            date_str = timezone.now().strftime(
                "%Y%m%d"
            )

            last_purchase = (
                Purchase.objects
                .filter(
                    purchase_number__startswith=(
                        f"PO-{date_str}-"
                    )
                )
                .order_by("-purchase_number")
                .first()
            )

            if last_purchase:

                try:

                    last_number = int(
                        last_purchase.purchase_number
                        .split("-")[-1]
                    )

                    new_number = last_number + 1

                except (
                    ValueError,
                    IndexError,
                ):

                    new_number = 1

            else:

                new_number = 1

            self.purchase_number = (
                f"PO-{date_str}-{new_number:04d}"
            )

        super().save(*args, **kwargs)

    # ==========================================================
    # RECEIVE PURCHASE
    # ==========================================================

    @transaction.atomic
    def receive(self, user=None):

        from apps.inventory.models import (
            Stock,
            StockMovement,
        )

        # ------------------------------------------------------
        # Lock purchase
        # ------------------------------------------------------

        purchase = (
            Purchase.objects
            .select_for_update()
            .get(pk=self.pk)
        )

        # ------------------------------------------------------
        # Prevent receiving cancelled purchase
        # ------------------------------------------------------

        if purchase.status == "cancelled":

            raise ValueError(
                "Cancelled purchase cannot be received."
            )

        # ------------------------------------------------------
        # Prevent receiving already fully received purchase
        # ------------------------------------------------------

        if purchase.status == "received":

            raise ValueError(
                "This purchase has already been received."
            )

        # ------------------------------------------------------
        # Get all purchase items
        # ------------------------------------------------------

        items = (
            PurchaseItem.objects
            .select_for_update()
            .select_related("product")
            .filter(purchase=purchase)
        )

        if not items.exists():

            raise ValueError(
                "Cannot receive a purchase without items."
            )

        total_received_now = 0

        # ======================================================
        # PROCESS EVERY ITEM
        # ======================================================

        for item in items:

            remaining = (
                item.quantity -
                item.received_quantity
            )

            # Nothing remaining
            if remaining <= 0:
                continue

            receive_quantity = remaining

            # --------------------------------------------------
            # Find or create stock
            # --------------------------------------------------

            stock, created = (
                Stock.objects
                .select_for_update()
                .get_or_create(
                    product=item.product,
                    branch=purchase.branch,
                    defaults={
                        "quantity": 0,
                    },
                )
            )

            # --------------------------------------------------
            # Previous stock
            # --------------------------------------------------

            previous_quantity = stock.quantity

            # --------------------------------------------------
            # Add stock
            # --------------------------------------------------

            stock.quantity = (
                stock.quantity +
                receive_quantity
            )

            stock.save(
                update_fields=[
                    "quantity",
                    "last_updated",
                ]
            )

            # --------------------------------------------------
            # New stock
            # --------------------------------------------------

            new_quantity = stock.quantity

            # --------------------------------------------------
            # Update received quantity
            # --------------------------------------------------

            item.received_quantity += (
                receive_quantity
            )

            item.save(
                update_fields=[
                    "received_quantity",
                ]
            )

            # --------------------------------------------------
            # Create movement
            # --------------------------------------------------

            StockMovement.objects.create(
                product=item.product,

                branch=purchase.branch,

                quantity=receive_quantity,

                previous_quantity=(
                    previous_quantity
                ),

                new_quantity=(
                    new_quantity
                ),

                movement_type="PURCHASE",

                reference=(
                    purchase.purchase_number
                ),

                notes=(
                    f"Stock received from "
                    f"purchase {purchase.purchase_number}"
                ),

                created_by=user,
            )

            total_received_now += (
                receive_quantity
            )

        # ======================================================
        # UPDATE PURCHASE STATUS
        # ======================================================

        all_items = (
            purchase.items.all()
        )

        total_ordered = sum(
            item.quantity
            for item in all_items
        )

        total_received = sum(
            item.received_quantity
            for item in all_items
        )

        if total_received >= total_ordered:

            purchase.status = "received"

            purchase.received_date = (
                timezone.now()
            )

        elif total_received > 0:

            purchase.status = (
                "partially_received"
            )

            purchase.received_date = (
                timezone.now()
            )

        purchase.save(
            update_fields=[
                "status",
                "received_date",
                "updated_at",
            ]
        )

        # ------------------------------------------------------
        # Update current object
        # ------------------------------------------------------

        self.status = purchase.status
        self.received_date = (
            purchase.received_date
        )

        return total_received_now

    # ==========================================================
    # RECEIVE SELECTED QUANTITIES
    # ==========================================================

    @transaction.atomic
    def receive_items(
        self,
        item_quantities,
        user=None,
    ):

        from apps.inventory.models import (
            Stock,
            StockMovement,
        )

        # ------------------------------------------------------
        # Lock purchase
        # ------------------------------------------------------

        purchase = (
            Purchase.objects
            .select_for_update()
            .get(pk=self.pk)
        )

        if purchase.status == "cancelled":

            raise ValueError(
                "Cancelled purchase cannot be received."
            )

        if purchase.status == "received":

            raise ValueError(
                "This purchase has already been fully received."
            )

        total_received_now = 0

        # ======================================================
        # PROCESS SELECTED ITEMS
        # ======================================================

        for item_id, requested_quantity in (
            item_quantities.items()
        ):

            try:

                receive_quantity = int(
                    requested_quantity
                )

            except (
                ValueError,
                TypeError,
            ):

                raise ValueError(
                    "Received quantity must be a valid number."
                )

            if receive_quantity <= 0:

                raise ValueError(
                    "Received quantity must be greater than zero."
                )

            # --------------------------------------------------
            # Get item
            # --------------------------------------------------

            try:

                item = (
                    PurchaseItem.objects
                    .select_for_update()
                    .select_related("product")
                    .get(
                        id=item_id,
                        purchase=purchase,
                    )
                )

            except PurchaseItem.DoesNotExist:

                raise ValueError(
                    f"Purchase item {item_id} does not exist."
                )

            # --------------------------------------------------
            # Remaining
            # --------------------------------------------------

            remaining = (
                item.quantity -
                item.received_quantity
            )

            if receive_quantity > remaining:

                raise ValueError(
                    f"Cannot receive {receive_quantity} "
                    f"units of {item.product.name}. "
                    f"Only {remaining} remaining."
                )

            # --------------------------------------------------
            # Stock
            # --------------------------------------------------

            stock, created = (
                Stock.objects
                .select_for_update()
                .get_or_create(
                    product=item.product,
                    branch=purchase.branch,
                    defaults={
                        "quantity": 0,
                    },
                )
            )

            previous_quantity = (
                stock.quantity
            )

            stock.quantity += (
                receive_quantity
            )

            stock.save(
                update_fields=[
                    "quantity",
                    "last_updated",
                ]
            )

            new_quantity = (
                stock.quantity
            )

            # --------------------------------------------------
            # Purchase item
            # --------------------------------------------------

            item.received_quantity += (
                receive_quantity
            )

            item.save(
                update_fields=[
                    "received_quantity",
                ]
            )

            # --------------------------------------------------
            # Movement
            # --------------------------------------------------

            StockMovement.objects.create(
                product=item.product,

                branch=purchase.branch,

                quantity=receive_quantity,

                previous_quantity=(
                    previous_quantity
                ),

                new_quantity=(
                    new_quantity
                ),

                movement_type="PURCHASE",

                reference=(
                    purchase.purchase_number
                ),

                notes=(
                    f"Stock received from "
                    f"purchase {purchase.purchase_number}"
                ),

                created_by=user,
            )

            total_received_now += (
                receive_quantity
            )

        # ======================================================
        # RECALCULATE PURCHASE STATUS
        # ======================================================

        all_items = (
            purchase.items.all()
        )

        total_ordered = sum(
            item.quantity
            for item in all_items
        )

        total_received = sum(
            item.received_quantity
            for item in all_items
        )

        if total_received >= total_ordered:

            purchase.status = "received"

            purchase.received_date = (
                timezone.now()
            )

        elif total_received > 0:

            purchase.status = (
                "partially_received"
            )

            purchase.received_date = (
                timezone.now()
            )

        purchase.save(
            update_fields=[
                "status",
                "received_date",
                "updated_at",
            ]
        )

        self.status = purchase.status
        self.received_date = (
            purchase.received_date
        )

        return total_received_now

    # ==========================================================
    # CANCEL PURCHASE
    # ==========================================================

    @transaction.atomic
    def cancel(self):

        if self.status == "received":

            raise ValueError(
                "A received purchase cannot be cancelled."
            )

        if self.status == "cancelled":

            raise ValueError(
                "Purchase is already cancelled."
            )

        self.status = "cancelled"

        self.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )


    class Meta:

        db_table = "purchases"

        ordering = [
            "-created_at"
        ]


# ==============================================================
# PURCHASE ITEM
# ==============================================================

class PurchaseItem(models.Model):

    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="purchase_items",
    )

    quantity = models.IntegerField(
        validators=[
            MinValueValidator(1)
        ]
    )

    received_quantity = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0)
        ]
    )

    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):

        return (
            f"{self.product.name} "
            f"x {self.quantity}"
        )

    class Meta:

        db_table = "purchase_items"

