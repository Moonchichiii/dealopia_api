# Generated by Django 5.1.6 on 2025-04-09 10:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0002_alter_cloudinaryimage_transformation_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cloudinaryimage",
            name="transformation_options",
            field=models.JSONField(
                blank=True,
                help_text="Additional Cloudinary transformation options",
                null=True,
            ),
        ),
    ]
