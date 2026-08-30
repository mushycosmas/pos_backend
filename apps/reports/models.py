from django.db import models

# Create your models here.
from django.db import models
from django.core.validators import MinValueValidator
from apps.companies.models import Company
from apps.branches.models import Branch
from apps.accounts.models import User

class ReportTemplate(models.Model):
    """Pre-defined report templates"""
    REPORT_TYPES = (
        ('sales', 'Sales Report'),
        ('inventory', 'Inventory Report'),
        ('purchase', 'Purchase Report'),
        ('financial', 'Financial Report'),
        ('customer', 'Customer Report'),
        ('supplier', 'Supplier Report'),
        ('expense', 'Expense Report'),
        ('tax', 'Tax Report'),
        ('profit_loss', 'Profit & Loss'),
        ('balance_sheet', 'Balance Sheet'),
        ('cash_flow', 'Cash Flow'),
        ('employee', 'Employee Report'),
        ('product', 'Product Performance'),
        ('branch', 'Branch Performance'),
    )
    
    FORMAT_CHOICES = (
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('html', 'HTML'),
        ('json', 'JSON'),
    )
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    
    # Configuration
    config = models.JSONField(default=dict)  # Store report configuration
    default_format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    
    # Permissions
    required_role = models.CharField(max_length=20, blank=True, null=True)  # Minimum role required
    is_system = models.BooleanField(default=False)  # System reports cannot be deleted
    is_active = models.BooleanField(default=True)
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"
    
    class Meta:
        db_table = 'report_templates'
        ordering = ['name']

class ReportSchedule(models.Model):
    """Scheduled report generation"""
    FREQUENCY_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    )
    
    DAYS_OF_WEEK = (
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
        ('sun', 'Sunday'),
    )
    
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='schedules')
    name = models.CharField(max_length=200)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    
    # Schedule details
    time = models.TimeField()
    day_of_week = models.CharField(max_length=3, choices=DAYS_OF_WEEK, null=True, blank=True)
    day_of_month = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MinValueValidator(31)])
    
    # Email settings
    send_email = models.BooleanField(default=True)
    email_recipients = models.JSONField(default=list)  # List of email addresses
    email_subject = models.CharField(max_length=200, blank=True)
    email_body = models.TextField(blank=True)
    
    # Output settings
    format = models.CharField(max_length=10, choices=ReportTemplate.FORMAT_CHOICES, default='pdf')
    include_charts = models.BooleanField(default=True)
    include_summary = models.BooleanField(default=True)
    
    # Filters
    filters = models.JSONField(default=dict)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.frequency}"
    
    class Meta:
        db_table = 'report_schedules'
        ordering = ['name']

class ReportHistory(models.Model):
    """History of generated reports"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    template = models.ForeignKey(ReportTemplate, on_delete=models.SET_NULL, null=True)
    schedule = models.ForeignKey(ReportSchedule, on_delete=models.SET_NULL, null=True, blank=True)
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=ReportTemplate.REPORT_TYPES)
    
    # Generation details
    format = models.CharField(max_length=10, choices=ReportTemplate.FORMAT_CHOICES)
    filters = models.JSONField(default=dict)
    
    # File storage
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    file_size = models.IntegerField(null=True, blank=True)  # Size in bytes
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # Metadata
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_reports')
    generated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Parameters used
    parameters = models.JSONField(default=dict)
    
    # Results summary
    row_count = models.IntegerField(default=0)
    summary = models.JSONField(default=dict, blank=True)
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.generated_at.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        db_table = 'report_history'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['generated_at']),
            models.Index(fields=['report_type']),
        ]

class DashboardWidget(models.Model):
    """Dashboard widgets configuration"""
    WIDGET_TYPES = (
        ('chart', 'Chart'),
        ('table', 'Table'),
        ('number', 'Number'),
        ('progress', 'Progress'),
        ('list', 'List'),
        ('calendar', 'Calendar'),
        ('map', 'Map'),
        ('custom', 'Custom'),
    )
    
    CHART_TYPES = (
        ('bar', 'Bar Chart'),
        ('line', 'Line Chart'),
        ('pie', 'Pie Chart'),
        ('doughnut', 'Doughnut Chart'),
        ('area', 'Area Chart'),
        ('scatter', 'Scatter Plot'),
        ('heatmap', 'Heatmap'),
    )
    
    name = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    chart_type = models.CharField(max_length=20, choices=CHART_TYPES, null=True, blank=True)
    
    # Configuration
    config = models.JSONField(default=dict)
    data_source = models.CharField(max_length=200)  # URL or function name
    
    # Size and position
    width = models.IntegerField(default=6)  # In grid columns (1-12)
    height = models.IntegerField(default=4)  # In grid rows
    
    # Colors and styling
    color = models.CharField(max_length=20, default='#3B82F6')
    background_color = models.CharField(max_length=20, default='#FFFFFF')
    
    # Permissions
    required_role = models.CharField(max_length=20, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'dashboard_widgets'
        ordering = ['name']

class DashboardLayout(models.Model):
    """User dashboard layouts"""
    LAYOUT_TYPES = (
        ('admin', 'Admin Dashboard'),
        ('manager', 'Manager Dashboard'),
        ('cashier', 'Cashier Dashboard'),
        ('storekeeper', 'Storekeeper Dashboard'),
        ('custom', 'Custom Dashboard'),
    )
    
    name = models.CharField(max_length=100)
    layout_type = models.CharField(max_length=20, choices=LAYOUT_TYPES, default='custom')
    description = models.TextField(blank=True)
    
    # Layout configuration
    widgets = models.JSONField(default=list)  # List of widget IDs and their positions
    columns = models.IntegerField(default=12)  # Grid columns
    spacing = models.IntegerField(default=10)  # Spacing in pixels
    
    # Permissions
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='dashboard_layouts')
    required_role = models.CharField(max_length=20, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_layout_type_display()})"
    
    class Meta:
        db_table = 'dashboard_layouts'
        ordering = ['name']

class ReportExport(models.Model):
    """Exported reports storage"""
    EXPORT_STATUS = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    )
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=ReportTemplate.REPORT_TYPES)
    
    # File information
    file = models.FileField(upload_to='reports/exports/')
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()  # Size in bytes
    format = models.CharField(max_length=10, choices=ReportTemplate.FORMAT_CHOICES)
    
    # Generation details
    filters = models.JSONField(default=dict)
    parameters = models.JSONField(default=dict)
    
    # Status
    status = models.CharField(max_length=20, choices=EXPORT_STATUS, default='pending')
    error_message = models.TextField(blank=True)
    
    # Access control
    is_public = models.BooleanField(default=False)
    access_token = models.CharField(max_length=100, unique=True, null=True, blank=True)
    expires_at = models.DateTimeField()
    
    # Metadata
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    downloaded_at = models.DateTimeField(null=True, blank=True)
    download_count = models.IntegerField(default=0)
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.format}"
    
    class Meta:
        db_table = 'report_exports'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['access_token']),
        ]

class ReportLog(models.Model):
    """Log of report actions"""
    ACTION_CHOICES = (
        ('view', 'Viewed'),
        ('generate', 'Generated'),
        ('export', 'Exported'),
        ('schedule', 'Scheduled'),
        ('email', 'Email Sent'),
        ('download', 'Downloaded'),
        ('delete', 'Deleted'),
    )
    
    report = models.ForeignKey(ReportHistory, on_delete=models.CASCADE, related_name='logs', null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    
    # Details
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # User
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'report_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action']),
            models.Index(fields=['created_at']),
        ]

class ReportMetric(models.Model):
    """Pre-calculated metrics for reports"""
    METRIC_TYPES = (
        ('sales', 'Sales Metric'),
        ('inventory', 'Inventory Metric'),
        ('customer', 'Customer Metric'),
        ('financial', 'Financial Metric'),
        ('employee', 'Employee Metric'),
        ('operational', 'Operational Metric'),
    )
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    
    # Calculation
    calculation = models.TextField()  # SQL or Python expression
    data_source = models.CharField(max_length=200)
    
    # Default values
    default_period = models.CharField(max_length=20, default='monthly')
    default_format = models.CharField(max_length=20, default='number')  # number, currency, percentage
    
    # Config
    config = models.JSONField(default=dict)
    
    is_active = models.BooleanField(default=True)
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        db_table = 'report_metrics'
        ordering = ['name']