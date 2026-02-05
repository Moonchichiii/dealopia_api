"""
Cloudinary storage integration for the CMS app.

This module provides a custom storage backend for Wagtail integration with Cloudinary.
Assumes Cloudinary is already configured via your settings/environment.
"""

from cloudinary import uploader
from cloudinary import utils as cloudinary_utils
from django.core.files.storage import Storage


class CloudinaryWagtailStorage(Storage):
    """
    Custom storage backend for Wagtail that uses Cloudinary with automatic image transformations.
    """

    def _open(self, name, mode="rb"):
        # Opening files directly from Cloudinary is not supported.
        raise NotImplementedError(
            "Opening files is not supported by CloudinaryWagtailStorage."
        )

    def _save(self, name, content):
        """
        Uploads the file content to Cloudinary with automatic optimizations and returns
        the Cloudinary public ID as the file name.
        """
        upload_result = uploader.upload(
            content,
            public_id=name,
            quality="auto",
            fetch_format="auto",
            responsive=True,
            format="auto",
            optimized_for_web=True,
        )
        return upload_result["public_id"]

    def exists(self, name):
        """
        Cloudinary does not offer a direct exists check.
        Returning False ensures that Django always uploads the file.
        """
        return False

    def url(self, name):
        """
        Generates and returns a URL for the stored file using Cloudinary's URL generation.
        """
        url, _ = cloudinary_utils.cloudinary_url(
            name,
            quality="auto",
            fetch_format="auto",
        )
        return url

    def delete(self, name):
        """
        Deletes the file from Cloudinary.
        """
        uploader.destroy(name)
