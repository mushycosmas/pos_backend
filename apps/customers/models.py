from django.db import models

# Create your models here.
from django.db import models
from django.core.validators import MinValueValidator
from apps.companies.models import Company
from apps.branches.models import Branch

class Customer(models.Model):
    CUSTOMER_TYPES = (
        ('individual', 'Individual'),
        ('business', 'Business'),
        ('wholesale', 'Wholesale'),
    )
    
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES, default='individual')
    tax_number = models.CharField(max_length=50, blank=True, null=True)
    
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    is_active = models.BooleanField(default=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='customers')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.phone})"
    
    class Meta:
        db_table = 'customers'
        ordering = ['name']