from django.db import models
from django.core.validators import MinValueValidator

class Company(models.Model):
    name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=200, blank=True)
    registration_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    tax_number = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Tanzania')
    logo = models.ImageField(upload_to='company/', blank=True, null=True)
    currency = models.CharField(max_length=3, default='TZS')
    timezone = models.CharField(max_length=50, default='Africa/Dar_es_Salaam')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'companies'
        ordering = ['name']
        verbose_name_plural = 'Companies'