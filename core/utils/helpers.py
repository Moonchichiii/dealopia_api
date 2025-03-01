import random
import string
from datetime import datetime, timedelta

def generate_random_code(length=8, chars=string.ascii_uppercase + string.digits):
    """Generate a random code of specified length"""
    return ''.join(random.choice(chars) for _ in range(length))

def is_valid_deal(start_date, end_date):
    """Check if a deal is currently valid based on start and end dates"""
    now = datetime.now()
    return start_date <= now <= end_date

def calculate_time_left(end_date):
    """Calculate time left until the end date"""
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
