from django.utils import timezone
import random
import string
import decimal
from decimal import Decimal

def generate_invoice_number(prefix='INV'):
    """
    Generate a unique invoice number.
    """
    date_str = timezone.now().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}-{date_str}-{random_str}"

def generate_sku(name, category=''):
    """
    Generate a SKU for a product.
    """
    # Take first 3 letters of name and category
    name_part = ''.join([c.upper() for c in name[:3] if c.isalpha()])
    cat_part = ''.join([c.upper() for c in category[:3] if c.isalpha()]) if category else ''
    random_part = ''.join(random.choices(string.digits, k=4))
    return f"{name_part}{cat_part}{random_part}".upper()

def calculate_discount(price, discount_value, discount_type='percentage'):
    """
    Calculate discount amount based on price.
    """
    if discount_type == 'percentage':
        return (price * discount_value) / 100
    else:  # fixed
        return discount_value

def calculate_tax(amount, tax_rate=0.18):
    """
    Calculate tax amount.
    """
    return amount * tax_rate

def format_currency(amount, currency='TZS'):
    """
    Format amount as currency.
    """
    return f"{currency} {amount:,.2f}"

def round_decimal(value, places=2):
    """
    Round decimal to specified places.
    """
    return Decimal(str(value)).quantize(Decimal('0.01'))

def get_client_ip(request):
    """
    Get client IP address from request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def generate_random_code(length=8):
    """
    Generate a random alphanumeric code.
    """
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def validate_phone_number(phone):
    """
    Validate phone number (Tanzania format).
    """
    # Remove any spaces or special characters
    phone = ''.join(filter(str.isdigit, phone))
    
    # Check if it's a valid Tanzania phone number
    if len(phone) == 9 and phone.startswith(('7', '6')):
        return True
    elif len(phone) == 10 and phone.startswith(('07', '06')):
        return True
    elif len(phone) == 12 and phone.startswith(('2557', '2556')):
        return True
    return False

def format_phone_number(phone):
    """
    Format phone number to standard format.
    """
    # Remove any spaces or special characters
    phone = ''.join(filter(str.isdigit, phone))
    
    # If it starts with 0, remove it and add 255
    if phone.startswith('0'):
        phone = '255' + phone[1:]
    # If it doesn't start with 255, add it
    elif not phone.startswith('255') and len(phone) == 9:
        phone = '255' + phone
    
    return phone