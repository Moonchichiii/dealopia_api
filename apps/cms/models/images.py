"""
Image models for the CMS app.

These models support Cloudinary integration for images in Wagtail.
"""

from django.conf import settings
from django.db import models
from cloudinary.models import CloudinaryField
from cloudinary.utils import cloudinary_url
from wagtail.images.models import AbstractImage, AbstractRendition, Image

# Default transformation settings
DEFAULT_TRANSFORMATION = {
    "quality": "auto",
    "fetch_format": "auto",
}

# Allow override via settings
CLOUDINARY_FOLDER = getattr(settings, "CLOUDINARY_FOLDER", "wagtail_images")
CLOUDINARY_DEFAULT_TRANSFORMATION = getattr(settings, "CLOUDINARY_DEFAULT_TRANSFORMATION", DEFAULT_TRANSFORMATION)


class CloudinaryImage(AbstractImage):
    """Wagtail Image model that uses Cloudinary for storage and transformations."""
    file = CloudinaryField(
        "image",
        folder=CLOUDINARY_FOLDER,
        transformation=CLOUDINARY_DEFAULT_TRANSFORMATION,
    )
    transformation_options = models.JSONField(
        blank=True,
        null=True,
        help_text="Additional Cloudinary transformation options"
    )
    admin_form_fields = Image.admin_form_fields

    class Meta(AbstractImage.Meta):
        verbose_name = "Image"
        verbose_name_plural = "Images"

    def get_rendition(self, filter_spec):
        """
        Create or retrieve a rendition using Cloudinary transformations.
        """
        width = None
        height = None
        crop = None

        # Parse filter spec
        if "width-" in filter_spec:
            width = int(filter_spec.split("width-")[1].split("-")[0])
        if "height-" in filter_spec:
            height = int(filter_spec.split("height-")[1].split("-")[0])
        if "crop-" in filter_spec:
            crop = filter_spec.split("crop-")[1].split("-")[0]

        options = CLOUDINARY_DEFAULT_TRANSFORMATION.copy()
        if width:
            options["width"] = width
        if height:
            options["height"] = height
        if crop:
            options["crop"] = crop

        if self.transformation_options:
            options.update(self.transformation_options)

        url, _ = cloudinary_url(self.file.public_id, **options)

        rendition, created = CloudinaryRendition.objects.get_or_create(
            image=self,
            filter_spec=filter_spec,
            focal_point_key=self.get_focal_point_key(),
            defaults={"file": url},
        )
        return rendition


class CloudinaryRendition(AbstractRendition):
    """
    Rendition model for CloudinaryImage that stores URLs instead of files.
    """
    image = models.ForeignKey(CloudinaryImage, on_delete=models.CASCADE, related_name="renditions")
    file = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = (("image", "filter_spec", "focal_point_key"),)

    def get_upload_to(self, filename):
        """Not used with Cloudinary storage."""
        return ""

    @property
    def url(self):
        """Return the Cloudinary URL for this rendition."""
        return self.file

    def get_storage(self):
        """Not used with Cloudinary storage."""
        return None
