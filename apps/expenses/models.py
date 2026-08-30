from django.db import models

# Create your models here.
from django.db import models
from django.core.validators import MinValueValidator
from apps.branches.models import Branch
from apps.companies.models import Company

class ExpenseCategory(models.Model):
    """Expense categories for organizing expenses"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'expense_categories'
        ordering = ['name']
        verbose_name_plural = 'Expense Categories'

class Expense(models.Model):
    """Expense records"""
    EXPENSE_TYPES = (
        ('operational', 'Operational'),
        ('utilities', 'Utilities'),
        ('salary', 'Salary'),
        ('rent', 'Rent'),
        ('transport', 'Transport'),
        ('maintenance', 'Maintenance'),
        ('marketing', 'Marketing'),
        ('food', 'Food & Beverage'),
        ('supplies', 'Office Supplies'),
        ('equipment', 'Equipment'),
        ('insurance', 'Insurance'),
        ('tax', 'Tax'),
        ('licenses', 'Licenses & Permits'),
        ('training', 'Training'),
        ('travel', 'Travel'),
        ('communication', 'Communication'),
        ('other', 'Other'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('overdue', 'Overdue'),
    )
    
    # Basic information
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, related_name='expenses')
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPES, default='other')
    
    # Financial details
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Date information
    expense_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    
    # Location
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='expenses')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, related_name='expenses')
    
    # Payment details
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    payment_date = models.DateField(null=True, blank=True)
    
    # References
    receipt = models.FileField(upload_to='expenses/receipts/', null=True, blank=True)
    invoice_number = models.CharField(max_length=100, blank=True, null=True)
    reference = models.CharField(max_length=100, blank=True, null=True)
    
    # Approval
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_expenses')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Rejection
    is_rejected = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True)
    rejected_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='rejected_expenses')
    rejected_at = models.DateTimeField(null=True, blank=True)
    
    # Creator
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='created_expenses')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.amount} ({self.expense_date})"
    
    def save(self, *args, **kwargs):
        if not self.total:
            self.total = self.amount + self.tax
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'expenses'
        ordering = ['-expense_date']
        indexes = [
            models.Index(fields=['expense_date']),
            models.Index(fields=['branch']),
            models.Index(fields=['category']),
            models.Index(fields=['payment_status']),
        ]

class RecurringExpense(models.Model):
    """Recurring expenses like rent, utilities, subscriptions"""
    FREQUENCY_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True)
    expense_type = models.CharField(max_length=20, choices=Expense.EXPENSE_TYPES, default='other')
    
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    next_due_date = models.DateField()
    
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True)
    
    is_active = models.BooleanField(default=True)
    auto_approve = models.BooleanField(default=False)
    
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.frequency}"
    
    def save(self, *args, **kwargs):
        if not self.total:
            self.total = self.amount + self.tax
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'recurring_expenses'
        ordering = ['-created_at']

class ExpenseBudget(models.Model):
    """Budget for expenses by category and period"""
    PERIOD_CHOICES = (
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    )
    
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE, related_name='budgets')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='monthly')
    year = models.IntegerField()
    month = models.IntegerField(null=True, blank=True)  # For monthly budgets
    quarter = models.IntegerField(null=True, blank=True)  # For quarterly budgets
    
    budgeted_amount = models.DecimalField(max_digits=12, decimal_places=2)
    actual_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.category.name} - {self.year} {self.get_period_display()}"
    
    def variance(self):
        """Calculate variance between budget and actual"""
        return self.budgeted_amount - self.actual_amount
    
    def variance_percentage(self):
        """Calculate variance percentage"""
        if self.budgeted_amount > 0:
            return (self.variance() / self.budgeted_amount) * 100
        return 0
    
    class Meta:
        db_table = 'expense_budgets'
        ordering = ['-year', '-month']
        unique_together = ['category', 'branch', 'period', 'year', 'month', 'quarter']

class ExpenseAttachment(models.Model):
    """Additional attachments for expenses"""
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='expenses/attachments/')
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField(null=True, blank=True)  # Size in bytes
    file_type = models.CharField(max_length=100, blank=True)
    
    uploaded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'expense_attachments'
        ordering = ['-uploaded_at']