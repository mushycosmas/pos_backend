from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from rest_framework import serializers

from .models import Sale, SaleItem

from apps.products.models import Product
from apps.products.serializers import ProductSerializer

from apps.customers.models import Customer
from apps.customers.serializers import CustomerSerializer

from apps.branches.models import Branch
from apps.branches.serializers import BranchSerializer

from apps.inventory.models import Stock, StockMovement


# =========================================================
# SALE ITEM SERIALIZER
# =========================================================

class SaleItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    product_sku = serializers.CharField(
        source="product.sku",
        read_only=True,
    )

    product_barcode = serializers.CharField(
        source="product.barcode",
        read_only=True,
    )

    product_details = ProductSerializer(
        source="product",
        read_only=True,
    )

    class Meta:
        model = SaleItem

        fields = [
            "id",
            "product",
            "product_name",
            "product_sku",
            "product_barcode",
            "product_details",
            "quantity",
            "unit_price",
            "discount",
            "tax",
            "total",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "product_name",
            "product_sku",
            "product_barcode",
            "product_details",
            "total",
            "created_at",
        ]


# =========================================================
# SALE LIST SERIALIZER
# =========================================================

class SaleListSerializer(serializers.ModelSerializer):

    branch_name = serializers.CharField(
        source="branch.name",
        read_only=True,
    )

    customer_display_name = serializers.SerializerMethodField()

    customer_display_phone = serializers.SerializerMethodField()

    created_by_name = serializers.SerializerMethodField()

    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Sale

        fields = [
            "id",
            "invoice_number",

            # Branch
            "branch",
            "branch_name",

            # Customer
            "customer",
            "customer_display_name",
            "customer_display_phone",

            # User
            "created_by",
            "created_by_name",

            # Amounts
            "subtotal",
            "discount",
            "tax_rate",
            "tax_amount",
            "total",

            # Payment
            "payment_method",
            "amount_paid",
            "change",
            "payment_phone",
            "transaction_reference",

            # Status
            "status",

            # Notes
            "notes",

            # Items
            "item_count",

            # Dates
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "invoice_number",
            "branch_name",
            "customer_display_name",
            "customer_display_phone",
            "created_by",
            "created_by_name",
            "item_count",
            "created_at",
            "updated_at",
        ]

    def get_customer_display_name(self, obj):

        return (
            obj.customer_name
            or (
                obj.customer.name
                if obj.customer
                else "Walk-in Customer"
            )
        )

    def get_customer_display_phone(self, obj):

        return (
            obj.customer_phone
            or (
                obj.customer.phone
                if obj.customer
                else None
            )
        )

    def get_created_by_name(self, obj):

        if not obj.created_by:
            return None

        full_name = obj.created_by.get_full_name()

        return (
            full_name
            or obj.created_by.username
        )

    def get_item_count(self, obj):

        return obj.items.count()


# =========================================================
# SALE DETAIL SERIALIZER
# =========================================================

class SaleDetailSerializer(serializers.ModelSerializer):

    items = SaleItemSerializer(
        many=True,
        read_only=True,
    )

    branch_details = BranchSerializer(
        source="branch",
        read_only=True,
    )

    customer_details = CustomerSerializer(
        source="customer",
        read_only=True,
    )

    created_by_name = serializers.SerializerMethodField()

    payment_status = serializers.SerializerMethodField()

    payments = serializers.SerializerMethodField()

    class Meta:
        model = Sale

        fields = [
            "id",
            "invoice_number",

            # Branch
            "branch",
            "branch_details",

            # Customer
            "customer",
            "customer_details",
            "customer_name",
            "customer_phone",

            # User
            "created_by",
            "created_by_name",

            # Amounts
            "subtotal",
            "discount",
            "tax_rate",
            "tax_amount",
            "total",

            # Payment
            "payment_method",
            "amount_paid",
            "change",
            "payment_phone",
            "transaction_reference",

            # Status
            "status",

            # Payment information
            "payment_status",
            "payments",

            # Notes
            "notes",

            # Items
            "items",

            # Dates
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "invoice_number",
            "branch_details",
            "customer_details",
            "created_by",
            "created_by_name",
            "payment_status",
            "payments",
            "items",
            "created_at",
            "updated_at",
        ]

    # =====================================================
    # CREATED BY
    # =====================================================

    def get_created_by_name(self, obj):

        if not obj.created_by:
            return None

        full_name = obj.created_by.get_full_name()

        return (
            full_name
            or obj.created_by.username
        )

    # =====================================================
    # PAYMENT STATUS
    # =====================================================

    def get_payment_status(self, obj):

        try:
            from apps.payments.models import Payment

            payments = Payment.objects.filter(
                sale=obj
            )

            if not payments.exists():
                return "pending"

            total_paid = sum(
                (
                    payment.amount
                    for payment in payments
                    if str(payment.status).upper()
                    in ["COMPLETED", "PAID"]
                ),
                Decimal("0.00"),
            )

            if total_paid >= obj.total:
                return "paid"

            if total_paid > Decimal("0.00"):
                return "partial"

            return "pending"

        except Exception:
            return "pending"

    # =====================================================
    # PAYMENTS
    # =====================================================

    def get_payments(self, obj):

        try:
            from apps.payments.models import Payment
            from apps.payments.serializers import PaymentSerializer

            payments = Payment.objects.filter(
                sale=obj
            )

            return PaymentSerializer(
                payments,
                many=True,
                context=self.context,
            ).data

        except Exception:
            return []


# =========================================================
# SALE CREATE SERIALIZER
# =========================================================

class SaleCreateSerializer(serializers.Serializer):

    # =====================================================
    # BRANCH
    # =====================================================

    branch_id = serializers.IntegerField()

    # =====================================================
    # CUSTOMER
    # =====================================================

    customer_id = serializers.IntegerField(
        required=False,
        allow_null=True,
    )

    customer_name = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=255,
    )

    customer_phone = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=20,
    )

    # =====================================================
    # ITEMS
    # =====================================================

    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
    )

    # =====================================================
    # DISCOUNT
    # =====================================================

    discount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
    )

    discount_type = serializers.ChoiceField(
        choices=[
            ("fixed", "Fixed"),
            ("percentage", "Percentage"),
        ],
        default="fixed",
    )

    # =====================================================
    # NOTES
    # =====================================================

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    # =====================================================
    # PAYMENT
    # =====================================================

    payment_method = serializers.ChoiceField(
        choices=[
            ("CASH", "Cash"),
            ("CARD", "Card"),
            ("M-PESA", "M-PESA"),
            ("TIGO-PESA", "Tigo Pesa"),
            ("AIRTEL-MONEY", "Airtel Money"),
            ("HALOPESA", "HaloPesa"),
            ("MIXX-BY-YAS", "Mixx by Yas"),
            ("EZY-PESA", "EzyPesa"),
            ("BANK_TRANSFER", "Bank Transfer"),
        ],
        required=False,
        default="CASH",
    )

    amount_paid = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
    )

    payment_phone = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=20,
    )

    transaction_reference = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=100,
    )

    # =====================================================
    # VALIDATE BRANCH
    # =====================================================

    def validate_branch_id(self, value):

        if not Branch.objects.filter(
            id=value,
            is_active=True,
        ).exists():

            raise serializers.ValidationError(
                "Branch not found or inactive."
            )

        return value

    # =====================================================
    # VALIDATE CUSTOMER
    # =====================================================

    def validate_customer_id(self, value):

        if value is None:
            return None

        if not Customer.objects.filter(
            id=value,
            is_active=True,
        ).exists():

            raise serializers.ValidationError(
                "Customer not found or inactive."
            )

        return value

    # =====================================================
    # VALIDATE ITEMS
    # =====================================================

    def validate_items(self, items):

        if not items:
            raise serializers.ValidationError(
                "At least one item is required."
            )

        branch_id = self.initial_data.get(
            "branch_id"
        )

        if not branch_id:
            raise serializers.ValidationError(
                "branch_id is required."
            )

        for index, item in enumerate(items):

            prefix = f"items[{index}]"

            # -------------------------------------------------
            # PRODUCT
            # -------------------------------------------------

            product_id = item.get(
                "product_id"
            )

            if not product_id:
                raise serializers.ValidationError({
                    prefix: "product_id is required."
                })

            try:
                product = Product.objects.get(
                    id=product_id,
                    is_active=True,
                )

            except Product.DoesNotExist:

                raise serializers.ValidationError({
                    prefix: (
                        f"Product with ID {product_id} "
                        "not found."
                    )
                })

            # -------------------------------------------------
            # QUANTITY
            # -------------------------------------------------

            quantity = item.get(
                "quantity"
            )

            if quantity is None:
                raise serializers.ValidationError({
                    prefix: "quantity is required."
                })

            try:
                quantity = int(quantity)

            except (TypeError, ValueError):

                raise serializers.ValidationError({
                    prefix: (
                        "Quantity must be a whole number."
                    )
                })

            if quantity <= 0:

                raise serializers.ValidationError({
                    prefix: (
                        "Quantity must be greater "
                        "than zero."
                    )
                })

            item["quantity"] = quantity

            # -------------------------------------------------
            # STOCK
            # -------------------------------------------------

            stock = (
                Stock.objects
                .filter(
                    product=product,
                    branch_id=branch_id,
                )
                .first()
            )

            if not stock:

                raise serializers.ValidationError({
                    prefix: (
                        f"No stock found for "
                        f"{product.name}."
                    )
                })

            available = stock.quantity

            if available < quantity:

                raise serializers.ValidationError({
                    prefix: (
                        f"Insufficient stock for "
                        f"{product.name}. "
                        f"Available: {available}."
                    )
                })

            # -------------------------------------------------
            # UNIT PRICE
            # -------------------------------------------------

            unit_price = item.get(
                "unit_price"
            )

            if unit_price in (
                None,
                "",
            ):

                unit_price = (
                    product.selling_price
                )

            try:

                unit_price = Decimal(
                    str(unit_price)
                )

            except Exception:

                raise serializers.ValidationError({
                    prefix: "Invalid unit_price."
                })

            if unit_price < Decimal("0.00"):

                raise serializers.ValidationError({
                    prefix: (
                        "Unit price cannot "
                        "be negative."
                    )
                })

            item["unit_price"] = unit_price

            # -------------------------------------------------
            # ITEM DISCOUNT
            # -------------------------------------------------

            item_discount = item.get(
                "discount",
                0,
            )

            try:

                item_discount = Decimal(
                    str(item_discount)
                )

            except Exception:

                raise serializers.ValidationError({
                    prefix: "Invalid discount."
                })

            if item_discount < Decimal("0.00"):

                raise serializers.ValidationError({
                    prefix: (
                        "Item discount cannot "
                        "be negative."
                    )
                })

            item["discount"] = item_discount

            # -------------------------------------------------
            # ITEM TAX
            # -------------------------------------------------

            item_tax = item.get(
                "tax",
                0,
            )

            try:

                item_tax = Decimal(
                    str(item_tax)
                )

            except Exception:

                raise serializers.ValidationError({
                    prefix: "Invalid tax."
                })

            if item_tax < Decimal("0.00"):

                raise serializers.ValidationError({
                    prefix: (
                        "Item tax cannot "
                        "be negative."
                    )
                })

            item["tax"] = item_tax

        return items

    # =====================================================
    # VALIDATE SALE
    # =====================================================

    def validate(self, data):

        discount = data.get(
            "discount",
            Decimal("0.00"),
        )

        discount_type = data.get(
            "discount_type",
            "fixed",
        )

        if discount < Decimal("0.00"):

            raise serializers.ValidationError({
                "discount": (
                    "Discount cannot be negative."
                )
            })

        subtotal = Decimal("0.00")

        for item in data["items"]:

            quantity = Decimal(
                str(item["quantity"])
            )

            unit_price = Decimal(
                str(item["unit_price"])
            )

            item_discount = Decimal(
                str(item.get("discount", 0))
            )

            item_subtotal = (
                quantity * unit_price
            )

            item_subtotal -= item_discount

            if item_subtotal < Decimal("0.00"):

                item_subtotal = Decimal("0.00")

            subtotal += item_subtotal

        # -------------------------------------------------
        # SALE DISCOUNT
        # -------------------------------------------------

        if (
            discount_type == "percentage"
            and discount > Decimal("100")
        ):

            raise serializers.ValidationError({
                "discount": (
                    "Percentage discount "
                    "cannot exceed 100%."
                )
            })

        if (
            discount_type == "fixed"
            and discount > subtotal
        ):

            raise serializers.ValidationError({
                "discount": (
                    "Fixed discount cannot "
                    "exceed subtotal."
                )
            })

        # -------------------------------------------------
        # PAYMENT
        # -------------------------------------------------

        amount_paid = data.get(
            "amount_paid",
            Decimal("0.00"),
        )

        if amount_paid < Decimal("0.00"):

            raise serializers.ValidationError({
                "amount_paid": (
                    "Amount paid cannot "
                    "be negative."
                )
            })

        data["subtotal"] = subtotal

        return data

    # =====================================================
    # CREATE SALE
    # =====================================================

    @transaction.atomic
    def create(self, validated_data):

        # =================================================
        # AUTHENTICATED USER
        # =================================================

        request = self.context.get(
            "request"
        )

        if not request:

            raise serializers.ValidationError(
                "Request context is required."
            )

        user = request.user

        if not user or not user.is_authenticated:

            raise serializers.ValidationError(
                "Authenticated user is required."
            )

        # =================================================
        # BASIC DATA
        # =================================================

        branch_id = validated_data["branch_id"]

        customer_id = validated_data.get(
            "customer_id"
        )

        customer_name = validated_data.get(
            "customer_name"
        )

        customer_phone = validated_data.get(
            "customer_phone"
        )

        items_data = validated_data["items"]

        discount = validated_data.get(
            "discount",
            Decimal("0.00"),
        )

        discount_type = validated_data.get(
            "discount_type",
            "fixed",
        )

        notes = validated_data.get(
            "notes",
            "",
        )

        payment_method = validated_data.get(
            "payment_method",
            "CASH",
        )

        amount_paid = validated_data.get(
            "amount_paid",
            Decimal("0.00"),
        )

        payment_phone = validated_data.get(
            "payment_phone"
        )

        transaction_reference = (
            validated_data.get(
                "transaction_reference"
            )
        )

        subtotal = validated_data["subtotal"]

        # =================================================
        # SALE DISCOUNT
        # =================================================

        if discount_type == "percentage":

            discount_amount = (
                subtotal
                * discount
                / Decimal("100")
            )

        else:

            discount_amount = discount

        # =================================================
        # TAX
        # =================================================

        taxable_amount = (
            subtotal
            - discount_amount
        )

        if taxable_amount < Decimal("0.00"):

            taxable_amount = Decimal("0.00")

        tax_rate = Decimal("18.00")

        tax_amount = (
            taxable_amount
            * tax_rate
            / Decimal("100")
        )

        # =================================================
        # TOTAL
        # =================================================

        total = (
            taxable_amount
            + tax_amount
        )

        # =================================================
        # CHANGE
        # =================================================

        change = (
            amount_paid
            - total
        )

        if change < Decimal("0.00"):

            change = Decimal("0.00")

        # =================================================
        # STATUS
        # =================================================

        if amount_paid >= total:

            sale_status = "COMPLETED"

        elif amount_paid > Decimal("0.00"):

            sale_status = "PENDING"

        else:

            sale_status = "PENDING"

        # =================================================
        # GET BRANCH
        # =================================================

        try:

            branch = Branch.objects.get(
                id=branch_id,
                is_active=True,
            )

        except Branch.DoesNotExist:

            raise serializers.ValidationError(
                "Branch not found or inactive."
            )

        # =================================================
        # GET CUSTOMER
        # =================================================

        customer = None

        if customer_id:

            try:

                customer = Customer.objects.get(
                    id=customer_id,
                    is_active=True,
                )

            except Customer.DoesNotExist:

                raise serializers.ValidationError(
                    "Customer not found or inactive."
                )

        # =================================================
        # CUSTOMER SNAPSHOT
        # =================================================

        if customer:

            customer_name = (
                customer_name
                or getattr(
                    customer,
                    "name",
                    None,
                )
            )

            customer_phone = (
                customer_phone
                or getattr(
                    customer,
                    "phone",
                    None,
                )
            )

        # =================================================
        # CREATE SALE
        # =================================================

        sale = Sale.objects.create(

            branch=branch,

            # IMPORTANT:
            # Never take created_by from frontend.
            # Always use the authenticated Django user.
            created_by=user,

            customer=customer,

            customer_name=customer_name,

            customer_phone=customer_phone,

            subtotal=subtotal,

            discount=discount_amount,

            tax_rate=tax_rate,

            tax_amount=tax_amount,

            total=total,

            payment_method=payment_method,

            amount_paid=amount_paid,

            change=change,

            payment_phone=payment_phone,

            transaction_reference=(
                transaction_reference
            ),

            status=sale_status,

            notes=notes,
        )

        # =================================================
        # CREATE ITEMS + UPDATE STOCK
        # =================================================

        for item_data in items_data:

            product_id = item_data["product_id"]

            quantity = int(
                item_data["quantity"]
            )

            unit_price = Decimal(
                str(item_data["unit_price"])
            )

            item_discount = Decimal(
                str(
                    item_data.get(
                        "discount",
                        0,
                    )
                )
            )

            item_tax = Decimal(
                str(
                    item_data.get(
                        "tax",
                        0,
                    )
                )
            )

            product = Product.objects.get(
                id=product_id,
                is_active=True,
            )

            # -------------------------------------------------
            # LOCK STOCK
            # -------------------------------------------------

            stock = (
                Stock.objects
                .select_for_update()
                .filter(
                    product=product,
                    branch_id=branch_id,
                )
                .first()
            )

            if not stock:

                raise serializers.ValidationError(
                    f"No stock found for "
                    f"{product.name}."
                )

            if stock.quantity < quantity:

                raise serializers.ValidationError(
                    f"Insufficient stock for "
                    f"{product.name}. "
                    f"Available: "
                    f"{stock.quantity}."
                )

            # -------------------------------------------------
            # ITEM TOTAL
            # -------------------------------------------------

            item_total = (
                Decimal(quantity)
                * unit_price
            )

            item_total -= item_discount

            item_total += item_tax

            if item_total < Decimal("0.00"):

                item_total = Decimal("0.00")

            # -------------------------------------------------
            # CREATE SALE ITEM
            # -------------------------------------------------

            SaleItem.objects.create(

                sale=sale,

                product=product,

                quantity=quantity,

                unit_price=unit_price,

                discount=item_discount,

                tax=item_tax,

                total=item_total,
            )

            # -------------------------------------------------
            # UPDATE STOCK
            # -------------------------------------------------

            old_quantity = stock.quantity

            stock.quantity = (
                stock.quantity - quantity
            )

            update_fields = [
                "quantity"
            ]

            if hasattr(
                stock,
                "last_updated",
            ):

                stock.last_updated = timezone.now()

                update_fields.append(
                    "last_updated"
                )

            stock.save(
                update_fields=update_fields
            )

            # -------------------------------------------------
            # STOCK MOVEMENT
            # -------------------------------------------------

            movement_data = {
                "product": product,
                "branch": branch,
                "quantity": -quantity,
                "previous_quantity": old_quantity,
                "new_quantity": stock.quantity,
                "movement_type": "SALE",
                "reference": (
                    f"Sale {sale.invoice_number}"
                ),
                "created_by": user,
            }

            if hasattr(
                StockMovement,
                "notes",
            ):

                movement_data["notes"] = (
                    f"Stock sold through "
                    f"sale {sale.invoice_number}"
                )

            StockMovement.objects.create(
                **movement_data
            )

        # =================================================
        # CREATE PAYMENT
        # =================================================

        if amount_paid > Decimal("0.00"):

            from apps.payments.models import Payment

            payment_data = {
                "sale": sale,
                "method": payment_method,
                "amount": amount_paid,
                "status": "COMPLETED",
                "payment_date": timezone.now(),
            }

            # -------------------------------------------------
            # OPTIONAL PAYMENT FIELDS
            # -------------------------------------------------

            payment_model_fields = {
                field.name
                for field in Payment._meta.get_fields()
            }

            if "reference" in payment_model_fields:

                payment_data["reference"] = (
                    transaction_reference or ""
                )

            if "processed_by" in payment_model_fields:

                payment_data["processed_by"] = user

            if "branch" in payment_model_fields:

                payment_data["branch"] = branch

            if "company" in payment_model_fields:

                payment_data["company"] = getattr(
                    branch,
                    "company",
                    None,
                )

            Payment.objects.create(
                **payment_data
            )

        return sale


# =========================================================
# SALE UPDATE SERIALIZER
# =========================================================

class SaleUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Sale

        fields = [
            "customer",
            "discount",
            "tax_rate",
            "payment_method",
            "amount_paid",
            "payment_phone",
            "transaction_reference",
            "notes",
            "status",
        ]

    def validate_status(self, value):

        instance = self.instance

        if not instance:
            return value

        if instance.status == "CANCELLED":

            raise serializers.ValidationError(
                "Cannot update a cancelled sale."
            )

        if instance.status == "REFUNDED":

            raise serializers.ValidationError(
                "Cannot update a refunded sale."
            )

        return value


# =========================================================
# SALE CANCEL SERIALIZER
# =========================================================

class SaleCancelSerializer(serializers.Serializer):

    reason = serializers.CharField(
        required=True,
        allow_blank=False,
    )

    def validate(self, data):

        sale = self.context.get(
            "sale"
        )

        if not sale:

            raise serializers.ValidationError(
                "Sale not found."
            )

        if sale.status == "CANCELLED":

            raise serializers.ValidationError(
                "Sale is already cancelled."
            )

        if sale.status == "REFUNDED":

            raise serializers.ValidationError(
                "Sale is already refunded."
            )

        return data


# =========================================================
# SALE RECEIPT SERIALIZER
# =========================================================

class SaleReceiptSerializer(serializers.Serializer):

    shop_name = serializers.CharField()

    shop_address = serializers.CharField()

    shop_phone = serializers.CharField()

    invoice_number = serializers.CharField()

    date = serializers.CharField()

    customer = serializers.CharField()

    items = serializers.ListField()

    subtotal = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    discount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    tax = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    total = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    payment_method = serializers.CharField()

    payment_amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    change = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    def to_representation(self, instance):

        sale = instance

        return {
            "shop_name": (
                sale.branch.name
                if sale.branch
                else ""
            ),

            "shop_address": (
                getattr(
                    sale.branch,
                    "location",
                    "",
                )
                if sale.branch
                else ""
            ),

            "shop_phone": (
                getattr(
                    sale.branch,
                    "phone",
                    "",
                )
                if sale.branch
                else ""
            ),

            "invoice_number": (
                sale.invoice_number
            ),

            "date": (
                sale.created_at.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            ),

            "customer": (
                sale.customer_name
                or (
                    sale.customer.name
                    if sale.customer
                    else "Walk-in Customer"
                )
            ),

            "items": [
                {
                    "name": item.product.name,
                    "quantity": item.quantity,
                    "unit_price": float(
                        item.unit_price
                    ),
                    "discount": float(
                        item.discount
                    ),
                    "tax": float(
                        item.tax
                    ),
                    "total": float(
                        item.total
                    ),
                }
                for item in sale.items.all()
            ],

            "subtotal": float(
                sale.subtotal
            ),

            "discount": float(
                sale.discount
            ),

            "tax": float(
                sale.tax_amount
            ),

            "total": float(
                sale.total
            ),

            "payment_method": (
                sale.payment_method
            ),

            "payment_amount": float(
                sale.amount_paid
            ),

            "change": float(
                sale.change
            ),
        }


# =========================================================
# SALE SUMMARY SERIALIZER
# =========================================================

class SaleSummarySerializer(serializers.Serializer):

    total_sales = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    total_orders = serializers.IntegerField()

    average_order_value = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    total_tax = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    total_discount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    top_products = serializers.ListField()

    sales_by_hour = serializers.DictField()

    sales_by_day = serializers.DictField()

    payment_methods = serializers.DictField()