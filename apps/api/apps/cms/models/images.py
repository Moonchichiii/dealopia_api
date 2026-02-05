"""
Image models for the CMS app.

These models support Cloudinary integration for images in Wagtail.
"""

import json

from cloudinary.models import CloudinaryField
from cloudinary.utils import cloudinary_url
from django.conf import settings
from django.db import models
from wagtail.images.models import AbstractImage, AbstractRendition, Image

# Default transformation settings
DEFAULT_TRANSFORMATION = {
    "quality": "auto",
    "fetch_format": "auto",
}


# Allow override via settings
CLOUDINARY_FOLDER = getattr(settings, "CLOUDINARY_FOLDER", "wagtail_images")
CLOUDINARY_DEFAULT_TRANSFORMATION = getattr(
    settings, "CLOUDINARY_DEFAULT_TRANSFORMATION", DEFAULT_TRANSFORMATION
)


class CloudinaryImage(AbstractImage):
    """Wagtail Image model that uses Cloudinary for storage and transformations."""

    file = CloudinaryField(
        "image",
        folder=CLOUDINARY_FOLDER,
        transformation=CLOUDINARY_DEFAULT_TRANSFORMATION,
    )
    # Using JSONField but with careful handling of dict values
    transformation_options = models.JSONField(
        blank=True, null=True, help_text="Additional Cloudinary transformation options"
    )
    admin_form_fields = Image.admin_form_fields

    class Meta(AbstractImage.Meta):
        verbose_name = "Image"
        verbose_name_plural = "Images"

    def save(self, *args, **kwargs):
        """
        Override save to ensure all dictionary values are properly serialized
        before they reach the database layer.
        """
        # Handle the transformation_options field
        if isinstance(self.transformation_options, dict):
            # Convert the dict to a serialized form that psycopg2 can handle
            # Even though it's a JSONField, sometimes it still needs help
            serialized_options = json.dumps(self.transformation_options)
            self.transformation_options = json.loads(serialized_options)

        # The critical part: ensure ALL dict values in file.options are serialized
        if (
            hasattr(self, "file")
            and hasattr(self.file, "options")
            and isinstance(self.file.options, dict)
        ):
            # Make a copy to avoid modifying during iteration
            options_copy = dict(self.file.options)

            # Process all keys that contain dictionaries
            for key, value in options_copy.items():
                if isinstance(value, dict):
                    self.file.options[key] = json.dumps(value)
                # Also check for nested dicts in lists
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            value[i] = json.dumps(item)

        super().save(*args, **kwargs)

    def get_transformation_options(self):
        """Get transformation options as a dictionary."""
        return self.transformation_options or {}

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

        # Apply custom transformations from model
        custom_options = self.get_transformation_options()
        if custom_options:
            options.update(custom_options)

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

    image = models.ForeignKey(
        CloudinaryImage, on_delete=models.CASCADE, related_name="renditions"
    )
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
