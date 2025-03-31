# Generated by Django 5.1.6 on 2025-03-25 23:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("deals", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="deal",
            name="eco_certifications",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="deal",
            name="sustainability_score",
            field=models.DecimalField(decimal_places=1, default=0, max_digits=3),
        ),
    ]
