from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from .models import Sale, SaleItem
from apps.products.models import Product
from apps.products.serializers import ProductSerializer
from apps.customers.models import Customer
from apps.customers.serializers import CustomerSerializer
from apps.branches.models import Branch
from apps.branches.serializers import BranchSerializer
from apps.inventory.models import Stock, StockMovement

class SaleItemSerializer(serializers.ModelSerializer):
    """Serializer for sale items"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_barcode = serializers.CharField(source='product.barcode', read_only=True)
    product_details = ProductSerializer(source='product', read_only=True)
    
    class Meta:
        model = SaleItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'product_barcode',
            'product_details', 'quantity', 'unit_price', 'discount', 'tax', 
            'total', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class SaleListSerializer(serializers.ModelSerializer):
    """Serializer for listing sales (lightweight)"""
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    cashier_name = serializers.CharField(source='cashier.get_full_name', read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Sale
        fields = [
            'id', 'invoice_number', 'branch', 'branch_name', 'customer', 
            'customer_name', 'customer_phone', 'cashier', 'cashier_name',
            'subtotal', 'discount', 'tax', 'total', 'status', 'notes',
            'item_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'invoice_number', 'created_at', 'updated_at']
    
    def get_item_count(self, obj):
        return obj.items.count()

class SaleDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed sale view"""
    items = SaleItemSerializer(many=True, read_only=True)
    branch_details = BranchSerializer(source='branch', read_only=True)
    customer_details = CustomerSerializer(source='customer', read_only=True)
    cashier_name = serializers.CharField(source='cashier.get_full_name', read_only=True)
    cashier_username = serializers.CharField(source='cashier.username', read_only=True)
    payment_status = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()
    
    class Meta:
        model = Sale
        fields = [
            'id', 'invoice_number', 'branch', 'branch_details', 'customer',
            'customer_details', 'cashier', 'cashier_name', 'cashier_username',
            'subtotal', 'discount', 'tax', 'total', 'status', 'payment_status',
            'payments', 'notes', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'invoice_number', 'created_at', 'updated_at']
    
    def get_payment_status(self, obj):
        """Get payment status for the sale"""
        from apps.payments.models import Payment
        payments = Payment.objects.filter(sale=obj)
        if not payments.exists():
            return 'pending'
        
        total_paid = sum(payment.amount for payment in payments.filter(status='completed'))
        if total_paid >= obj.total:
            return 'paid'
        elif total_paid > 0:
            return 'partial'
        return 'pending'
    
    def get_payments(self, obj):
        """Get payment details"""
        from apps.payments.models import Payment
        from apps.payments.serializers import PaymentSerializer
        payments = Payment.objects.filter(sale=obj)
        return PaymentSerializer(payments, many=True).data

class SaleCreateSerializer(serializers.Serializer):
    """Serializer for creating a new sale"""
    branch_id = serializers.IntegerField()
    customer_id = serializers.IntegerField(required=False, allow_null=True)
    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )
    discount = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_type = serializers.ChoiceField(choices=[('percentage', 'Percentage'), ('fixed', 'Fixed')], default='fixed')
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_branch_id(self, value):
        """Validate branch exists and is active"""
        try:
            branch = Branch.objects.get(id=value, is_active=True)
        except Branch.DoesNotExist:
            raise serializers.ValidationError("Branch not found or inactive")
        return value
    
    def validate_customer_id(self, value):
        """Validate customer exists and is active"""
        if value:
            try:
                customer = Customer.objects.get(id=value, is_active=True)
            except Customer.DoesNotExist:
                raise serializers.ValidationError("Customer not found or inactive")
        return value
    
    def validate_items(self, value):
        """Validate items and check stock availability"""
        if not value:
            raise serializers.ValidationError("At least one item is required")
        
        branch_id = self.initial_data.get('branch_id')
        
        for idx, item in enumerate(value):
            # Validate required fields
            if 'product_id' not in item:
                raise serializers.ValidationError({
                    f'items[{idx}]': 'product_id is required'
                })
            
            if 'quantity' not in item:
                raise serializers.ValidationError({
                    f'items[{idx}]': 'quantity is required'
                })
            
            # Validate product exists
            try:
                product = Product.objects.get(id=item['product_id'], is_active=True)
            except Product.DoesNotExist:
                raise serializers.ValidationError({
                    f'items[{idx}]': f"Product with ID {item['product_id']} not found"
                })
            
            # Validate quantity
            quantity = item['quantity']
            if quantity <= 0:
                raise serializers.ValidationError({
                    f'items[{idx}]': "Quantity must be greater than zero"
                })
            
            # Check stock availability
            if branch_id:
                stock = Stock.objects.filter(product=product, branch_id=branch_id).first()
                if not stock or stock.quantity < quantity:
                    raise serializers.ValidationError({
                        f'items[{idx}]': f"Insufficient stock for {product.name}. Available: {stock.quantity if stock else 0}"
                    })
            
            # Validate unit price
            if 'unit_price' not in item:
                item['unit_price'] = product.selling_price
            
            unit_price = item['unit_price']
            if unit_price <= 0:
                raise serializers.ValidationError({
                    f'items[{idx}]': "Unit price must be greater than zero"
                })
        
        return value
    
    def validate(self, data):
        """Validate total discount"""
        discount = data.get('discount', 0)
        discount_type = data.get('discount_type', 'fixed')
        
        if discount < 0:
            raise serializers.ValidationError({
                'discount': "Discount cannot be negative"
            })
        
        # Calculate subtotal to validate discount
        subtotal = 0
        items = data.get('items', [])
        for item in items:
            quantity = item.get('quantity', 0)
            unit_price = item.get('unit_price', 0)
            subtotal += quantity * unit_price
        
        if discount_type == 'percentage' and discount > 100:
            raise serializers.ValidationError({
                'discount': "Percentage discount cannot exceed 100%"
            })
        
        if discount_type == 'fixed' and discount > subtotal:
            raise serializers.ValidationError({
                'discount': "Fixed discount cannot exceed subtotal"
            })
        
        data['subtotal'] = subtotal
        return data

    def create(self, validated_data):
        """Create a new sale with items"""
        from apps.payments.models import Payment
        
        request = self.context.get('request')
        user = request.user if request else None
        
        branch_id = validated_data['branch_id']
        customer_id = validated_data.get('customer_id')
        items_data = validated_data['items']
        discount = validated_data.get('discount', 0)
        discount_type = validated_data.get('discount_type', 'fixed')
        notes = validated_data.get('notes', '')
        subtotal = validated_data['subtotal']
        
        # Calculate discount amount
        if discount_type == 'percentage':
            discount_amount = (discount / 100) * subtotal
        else:
            discount_amount = discount
        
        # Calculate tax (assuming 18% VAT)
        tax_rate = 0.18
        tax = (subtotal - discount_amount) * tax_rate
        
        # Calculate total
        total = subtotal - discount_amount + tax
        
        with transaction.atomic():
            # Create sale
            sale = Sale.objects.create(
                branch_id=branch_id,
                customer_id=customer_id,
                cashier=user,
                subtotal=subtotal,
                discount=discount_amount,
                tax=tax,
                total=total,
                status='completed',
                notes=notes
            )
            
            # Create sale items and update stock
            sale_items = []
            for item_data in items_data:
                product_id = item_data['product_id']
                quantity = item_data['quantity']
                unit_price = item_data.get('unit_price', 0)
                
                # Get product
                product = Product.objects.get(id=product_id)
                
                # Calculate item total
                item_discount = 0  # Could implement per-item discount
                item_tax = 0
                item_total = quantity * unit_price
                
                # Create sale item
                sale_item = SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    discount=item_discount,
                    tax=item_tax,
                    total=item_total
                )
                sale_items.append(sale_item)
                
                # Update stock
                stock = Stock.objects.filter(product=product, branch_id=branch_id).first()
                if stock:
                    old_quantity = stock.quantity
                    stock.quantity -= quantity
                    stock.save()
                    
                    # Create stock movement
                    StockMovement.objects.create(
                        product=product,
                        branch_id=branch_id,
                        quantity=-quantity,
                        previous_quantity=old_quantity,
                        new_quantity=stock.quantity,
                        movement_type='SALE',
                        reference=f'Sale {sale.invoice_number}',
                        created_by=user,
                        company=product.company
                    )
            
            # Create payment if method provided
            payment_data = self.context.get('payment_data')
            if payment_data:
                Payment.objects.create(
                    sale=sale,
                    method=payment_data.get('method', 'cash'),
                    amount=payment_data.get('amount', total),
                    reference=payment_data.get('reference', ''),
                    status='completed',
                    payment_date=timezone.now(),
                    processed_by=user,
                    company=sale.branch.company if hasattr(sale.branch, 'company') else None,
                    branch=sale.branch
                )
            
            return sale

class SaleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a sale"""
    class Meta:
        model = Sale
        fields = ['customer', 'discount', 'tax', 'notes', 'status']
    
    def validate_status(self, value):
        """Validate status transition"""
        instance = self.instance
        if instance and instance.status == 'completed' and value == 'cancelled':
            # Allow cancellation of completed sales
            pass
        elif instance and instance.status == 'cancelled':
            raise serializers.ValidationError("Cannot update a cancelled sale")
        return value

class SaleCancelSerializer(serializers.Serializer):
    """Serializer for cancelling a sale"""
    reason = serializers.CharField(required=True)
    
    def validate(self, data):
        """Validate sale can be cancelled"""
        sale = self.context.get('sale')
        if not sale:
            raise serializers.ValidationError("Sale not found")
        
        if sale.status == 'cancelled':
            raise serializers.ValidationError("Sale is already cancelled")
        
        if sale.status == 'refunded':
            raise serializers.ValidationError("Sale is already refunded")
        
        return data

class SaleReceiptSerializer(serializers.Serializer):
    """Serializer for generating receipt data"""
    shop_name = serializers.CharField()
    shop_address = serializers.CharField()
    shop_phone = serializers.CharField()
    invoice_number = serializers.CharField()
    date = serializers.CharField()
    cashier = serializers.CharField()
    customer = serializers.CharField()
    items = serializers.ListField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    discount = serializers.DecimalField(max_digits=12, decimal_places=2)
    tax = serializers.DecimalField(max_digits=12, decimal_places=2)
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_method = serializers.CharField()
    payment_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    change = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    def to_representation(self, instance):
        """Convert sale instance to receipt data"""
        from apps.payments.models import Payment
        
        sale = instance
        payments = Payment.objects.filter(sale=sale, status='completed')
        total_paid = sum(payment.amount for payment in payments) if payments else 0
        
        return {
            'shop_name': sale.branch.name,
            'shop_address': sale.branch.location,
            'shop_phone': sale.branch.phone,
            'invoice_number': sale.invoice_number,
            'date': sale.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'cashier': sale.cashier.get_full_name() if sale.cashier else 'N/A',
            'customer': sale.customer.name if sale.customer else 'Walk-in Customer',
            'items': [
                {
                    'name': item.product.name,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'discount': float(item.discount),
                    'tax': float(item.tax),
                    'total': float(item.total)
                }
                for item in sale.items.all()
            ],
            'subtotal': float(sale.subtotal),
            'discount': float(sale.discount),
            'tax': float(sale.tax),
            'total': float(sale.total),
            'payment_method': payments.first().method if payments else 'N/A',
            'payment_amount': float(total_paid),
            'change': float(total_paid - sale.total) if total_paid > sale.total else 0
        }

class SaleSummarySerializer(serializers.Serializer):
    """Serializer for sales summary/dashboard"""
    total_sales = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_orders = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_tax = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_discount = serializers.DecimalField(max_digits=12, decimal_places=2)
    top_products = serializers.ListField()
    sales_by_hour = serializers.DictField()
    sales_by_day = serializers.DictField()
    payment_methods = serializers.DictField()