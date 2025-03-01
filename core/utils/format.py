from decimal import Decimal

def format_currency(amount, currency='$'):
    """Format a decimal amount as currency"""
    if amount is None:
        return None
    
    return f"{currency}{amount:.2f}"

def calculate_discount_percentage(original, discounted):
    """Calculate discount percentage from original and discounted prices"""
    if original <= 0:
        return 0
    
    return int(((original - discounted) / original) * 100)

def format_address(address_parts):
    """Format an address from its parts"""
    filtered_parts = [p for p in address_parts if p]
    return ", ".join(filtered_parts)

def format_file_size(size_bytes):
    """Format file size from bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024 or unit == 'GB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
