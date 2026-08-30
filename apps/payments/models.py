from django.db import models
from django.core.validators import MinValueValidator
from apps.sales.models import Sale
from apps.companies.models import Company
from apps.branches.models import Branch

class PaymentMethod(models.Model):
    """Payment methods configuration"""
    PAYMENT_TYPES = (
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('card', 'Card Payment'),
        ('mobile_money', 'Mobile Money'),
        ('cheque', 'Cheque'),
        ('credit', 'Credit'),
        ('other', 'Other'),
    )
    
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, unique=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    is_active = models.BooleanField(default=True)
    requires_reference = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        db_table = 'payment_methods'
        ordering = ['name']

class Payment(models.Model):
    """Payment transactions"""
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('card', 'Card Payment'),
        ('mpesa', 'M-Pesa'),
        ('airtel_money', 'Airtel Money'),
        ('tigo_pesa', 'Tigo Pesa'),
        ('halopesa', 'HaloPesa'),
        ('cheque', 'Cheque'),
        ('credit', 'Credit'),
        ('other', 'Other'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    )
    
    PAYMENT_DIRECTION = (
        ('incoming', 'Incoming'),  # Customer pays us
        ('outgoing', 'Outgoing'),  # We pay supplier
    )
    
    # Relationships
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    purchase = models.ForeignKey('purchases.Purchase', on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Payment details
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    direction = models.CharField(max_length=20, choices=PAYMENT_DIRECTION, default='incoming')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    currency = models.CharField(max_length=3, default='TZS')
    
    # Reference details
    reference = models.CharField(max_length=100, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Payment gateway details
    gateway = models.CharField(max_length=50, blank=True, null=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Dates
    payment_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional info
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='processed_payments')
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_payments')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_method_display()} - {self.amount} - {self.status}"
    
    def save(self, *args, **kwargs):
        # Set branch from sale or purchase if not set
        if not self.branch:
            if self.sale:
                self.branch = self.sale.branch
            elif self.purchase:
                self.branch = self.purchase.branch
        
        # Set company from sale or purchase if not set
        if not self.company and self.sale:
            self.company = self.sale.company
        elif not self.company and self.purchase:
            self.company = self.purchase.company
        
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['reference']),
            models.Index(fields=['status']),
        ]

class PaymentGateway(models.Model):
    """Payment gateway configurations"""
    GATEWAY_TYPES = (
        ('mobile_money', 'Mobile Money'),
        ('bank', 'Bank'),
        ('card', 'Card'),
        ('wallet', 'Wallet'),
        ('other', 'Other'),
    )
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    gateway_type = models.CharField(max_length=20, choices=GATEWAY_TYPES)
    
    # API Configuration
    api_url = models.URLField()
    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.CharField(max_length=255, blank=True)
    merchant_id = models.CharField(max_length=100, blank=True)
    callback_url = models.URLField(blank=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_test_mode = models.BooleanField(default=False)
    test_api_url = models.URLField(blank=True)
    test_api_key = models.CharField(max_length=255, blank=True)
    test_api_secret = models.CharField(max_length=255, blank=True)
    test_merchant_id = models.CharField(max_length=100, blank=True)
    
    # Supported methods
    supported_methods = models.JSONField(default=list)
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'payment_gateways'
        ordering = ['name']

class PaymentTransactionLog(models.Model):
    """Log for payment transactions"""
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='logs')
    
    action = models.CharField(max_length=50)
    request_data = models.JSONField(default=dict)
    response_data = models.JSONField(default=dict)
    status = models.CharField(max_length=20)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payment_transaction_logs'
        ordering = ['-created_at']

class PaymentBatch(models.Model):
    """Batch payments (for payroll, supplier payments, etc.)"""
    BATCH_STATUS = (
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    )
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    batch_type = models.CharField(max_length=50)  # payroll, supplier, refund, etc.
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_items = models.IntegerField(default=0)
    
    status = models.CharField(max_length=20, choices=BATCH_STATUS, default='draft')
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='created_batches')
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_batches')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.total_amount}"
    
    class Meta:
        db_table = 'payment_batches'
        ordering = ['-created_at']