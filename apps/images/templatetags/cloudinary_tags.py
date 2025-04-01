from django import template
from cloudinary.utils import cloudinary_url

register = template.Library()

@register.simple_tag
def cloudinary_image(image, width=None, height=None, crop=None, **kwargs):
    """
    Generate a Cloudinary URL for an image with transformations.
    
    Args:
        image: The Cloudinary image object
        width: Optional width for resizing
        height: Optional height for resizing
        crop: Optional crop mode
        **kwargs: Additional Cloudinary transformation options
        
    Returns:
        str: The generated Cloudinary URL or empty string if no image
    """
    if not image:
        return ''
    
    # Set up basic transformations
    options = {
        'quality': 'auto',
        'fetch_format': 'auto',
    }
    
    # Add dimensions if provided
    if width:
        options['width'] = width
    if height:
        options['height'] = height
    if crop:
        options['crop'] = crop
    
    # Add any additional transformations
    options.update(kwargs)
    
    # Get the Cloudinary URL
    url, _ = cloudinary_url(image.file.public_id, **options)
    
    return url