from django.db import models
from wagtail.images.models import Image, AbstractImage, AbstractRendition
from cloudinary.models import CloudinaryField
from cloudinary.utils import cloudinary_url


class CloudinaryImage(AbstractImage):
    """Wagtail Image model that uses Cloudinary for storage and transformations."""
    file = CloudinaryField(
        'image',
        folder='wagtail_images/',
        transformation={
            'quality': 'auto',
            'fetch_format': 'auto',
        }
    )
    
    transformation_options = models.JSONField(
        blank=True, 
        null=True,
        help_text="Additional Cloudinary transformation options"
    )
    
    admin_form_fields = Image.admin_form_fields
    
    class Meta(AbstractImage.Meta):
        verbose_name = 'Image'
        verbose_name_plural = 'Images'
    
    def get_rendition(self, filter_spec):
        """
        Create or retrieve a rendition using Cloudinary transformations.
        
        Args:
            filter_spec: String specifying the desired image transformations.
        
        Returns:
            CloudinaryRendition object with the transformed image URL.
        """
        width = None
        height = None
        crop = None
        
        # Parse filter spec to extract dimensions and crop mode
        if 'width-' in filter_spec:
            width = int(filter_spec.split('width-')[1].split('-')[0])
        if 'height-' in filter_spec:
            height = int(filter_spec.split('height-')[1].split('-')[0])
        if 'crop-' in filter_spec:
            crop = filter_spec.split('crop-')[1].split('-')[0]
        
        # Build Cloudinary transformation URL
        options = {
            'quality': 'auto',
            'fetch_format': 'auto',
        }
        
        if width:
            options['width'] = width
        if height:
            options['height'] = height
        if crop:
            options['crop'] = crop
        
        # Add any custom transformations specified for this image
        if self.transformation_options:
            options.update(self.transformation_options)
        
        # Generate URL
        url, _ = cloudinary_url(self.file.public_id, **options)
        
        # Create or get rendition object
        rendition, created = CloudinaryRendition.objects.get_or_create(
            image=self,
            filter_spec=filter_spec,
            focal_point_key=self.get_focal_point_key(),
            defaults={'file': url}
        )
        
        return rendition


class CloudinaryRendition(AbstractRendition):
    """
    Rendition model for CloudinaryImage that stores URLs instead of files.
    """
    image = models.ForeignKey(
        CloudinaryImage, 
        on_delete=models.CASCADE, 
        related_name='renditions'
    )
    file = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = (
            ('image', 'filter_spec', 'focal_point_key'),
        )
    
    def get_upload_to(self, filename):
        """Not used with Cloudinary storage."""
        return ''
    
    @property
    def url(self):
        """Return the Cloudinary URL for this rendition."""
        return self.file
    
    def get_storage(self):
        """Not used with Cloudinary storage."""
        return None