# Generated by Django 5.1.6

import json

from django.db import migrations, models


def convert_dict_to_json(apps, schema_editor):
    """Convert any dict values in transformation_options to JSON strings."""
    CloudinaryImage = apps.get_model("cms", "CloudinaryImage")
    for image in CloudinaryImage.objects.all():
        if image.transformation_options and isinstance(
            image.transformation_options, dict
        ):
            image.transformation_options = json.dumps(image.transformation_options)
            image.save(update_fields=["transformation_options"])


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cloudinaryimage",
            name="transformation_options",
            field=models.TextField(
                blank=True,
                help_text="Additional Cloudinary transformation options (JSON format)",
                null=True,
            ),
        ),
        migrations.RunPython(convert_dict_to_json, migrations.RunPython.noop),
    ]
