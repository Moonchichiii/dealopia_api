import cloudinary
from cloudinary.utils import cloudinary_url
from django.core.files.storage import Storage
from django.conf import settings
from wagtail.images.models import AbstractImage, AbstractRendition, Image

class CloudinaryWagtailStorage(Storage):
    """
    Custom storage backend for Wagtail that uses Cloudinary
    with automatic image transformations
    """

    def __init__(self):
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
            api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
            api_secret=settings.CLOUDINARY_STORAGE['API_SECRET'],
            secure=True
        )
        
    def save(self, name, content, max_length=None):
        # Upload to Cloudinary with optimizations
        upload_result = cloudinary.uploader.upload(
            content,
            public_id=name,
            # Enable auto-optimization features
            quality="auto",
            fetch_format="auto",
            # Enable responsive images
            responsive=True,
            # Enable automatic format conversion
            format="auto",
            # Additional optimizations
            optimized_for_web=True,
            # Enable automatic background removal (optional)
            # background_removal="cloudinary_ai",
            # Other transformations can be added here
        )
        
        return upload_result["public_id"]