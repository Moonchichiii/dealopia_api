# Generated by Django 5.1.6 on 2025-03-25 23:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ScraperJob",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("spider_name", models.CharField(max_length=100)),
                ("status", models.CharField(default="pending", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Scraper Job",
                "verbose_name_plural": "Scraper Jobs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ScrapedDeal",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("url", models.URLField()),
                ("is_valid", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "job",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="deals",
                        to="scrapers.scraperjob",
                    ),
                ),
            ],
            options={
                "verbose_name": "Scraped Deal",
                "verbose_name_plural": "Scraped Deals",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ScraperProxy",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("host", models.CharField(max_length=100)),
                ("port", models.IntegerField()),
                ("is_active", models.BooleanField(default=True)),
                ("failure_count", models.IntegerField(default=0)),
            ],
            options={
                "verbose_name": "Scraper Proxy",
                "verbose_name_plural": "Scraper Proxies",
                "unique_together": {("host", "port")},
            },
        ),
    ]
