from datetime import datetime
from decimal import Decimal
import random
import string


def format_currency(amount, currency='$'):
    """Format a decimal amount as currency."""
    if amount is None:
        return None
    
    return f"{currency}{amount:.2f}"


def calculate_discount_percentage(original, discounted):
    """Calculate discount percentage from original and discounted prices."""
    if original <= 0:
        return 0
    
    return int(((original - discounted) / original) * 100)


def format_address(address_parts):
    """Format an address from its parts."""
    filtered_parts = [p for p in address_parts if p]
    return ", ".join(filtered_parts)


def format_file_size(size_bytes):
    """Format file size from bytes to human-readable format."""
    if size_bytes < 0:
        return "0 B"
        
    units = ['B', 'KB', 'MB', 'GB']
    unit_index = 0
    
    while size_bytes >= 1024 and unit_index < len(units) - 1:
        size_bytes /= 1024
        unit_index += 1
        
    return f"{size_bytes:.2f} {units[unit_index]}"


def generate_random_code(length=8, chars=string.ascii_uppercase + string.digits):
    """Generate a random code of specified length."""
    return ''.join(random.choice(chars) for _ in range(length))


def is_valid_deal(start_date, end_date):
    """Check if a deal is currently valid based on start and end dates."""
    now = datetime.now()
    return start_date <= now <= end_date


def calculate_time_left(end_date):
    """Calculate time left until the end date."""
    now = datetime.now()
    if end_date <= now:
        return "Expired"
    
    delta = end_date - now
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"{days} days, {hours} hours"
    elif hours > 0:
        return f"{hours} hours, {minutes} minutes"
    else:
        return f"{minutes} minutes"


def humanize_time_ago(date):
    """Convert a past date to a human-readable time ago format."""
    now = datetime.now()
    delta = now - date
    
    if delta.days > 365:
        years = delta.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"
    elif delta.days > 30:
        months = delta.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    elif delta.days > 0:
        return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
    elif delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif delta.seconds > 60:
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"