# Generated by Django 5.1.6 on 2025-04-01 20:58

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

import apps.products.models


class Migration(migrations.Migration):

    dependencies = [
        ("categories", "0002_remove_category_icon_category_is_eco_friendly_and_more"),
        ("products", "0001_initial"),
        ("shops", "0005_alter_shop_banner_image"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="product",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Product",
                "verbose_name_plural": "Products",
            },
        ),
        migrations.AddField(
            model_name="product",
            name="additional_images",
            field=models.JSONField(
                blank=True, default=list, null=True, verbose_name="Additional Images"
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="barcode",
            field=models.CharField(blank=True, max_length=50, verbose_name="Barcode"),
        ),
        migrations.AddField(
            model_name="product",
            name="categories",
            field=models.ManyToManyField(
                blank=True,
                related_name="products",
                to="categories.category",
                verbose_name="Categories",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="dimensions",
            field=models.JSONField(
                blank=True,
                default=apps.products.models.default_dimensions,
                help_text="JSON object with length, width, and height in cm",
                null=True,
                verbose_name="Dimensions (cm)",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="discount_percentage",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=5,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(100),
                ],
                verbose_name="Discount Percentage",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="is_available",
            field=models.BooleanField(default=True, verbose_name="Available"),
        ),
        migrations.AddField(
            model_name="product",
            name="is_featured",
            field=models.BooleanField(default=False, verbose_name="Featured"),
        ),
        migrations.AddField(
            model_name="product",
            name="meta_description",
            field=models.CharField(
                blank=True, max_length=255, verbose_name="Meta Description"
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="meta_title",
            field=models.CharField(
                blank=True, max_length=255, verbose_name="Meta Title"
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="purchase_count",
            field=models.PositiveIntegerField(default=0, verbose_name="Purchase Count"),
        ),
        migrations.AddField(
            model_name="product",
            name="sku",
            field=models.CharField(
                blank=True, max_length=50, null=True, unique=True, verbose_name="SKU"
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="specifications",
            field=models.JSONField(
                blank=True, default=dict, null=True, verbose_name="Specifications"
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="view_count",
            field=models.PositiveIntegerField(default=0, verbose_name="View Count"),
        ),
        migrations.AddField(
            model_name="product",
            name="weight",
            field=models.DecimalField(
                decimal_places=3, default=0, max_digits=8, verbose_name="Weight"
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="weight_unit",
            field=models.CharField(
                choices=[
                    ("g", "Grams"),
                    ("kg", "Kilograms"),
                    ("lb", "Pounds"),
                    ("oz", "Ounces"),
                ],
                default="g",
                max_length=2,
                verbose_name="Weight Unit",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
        ),
        migrations.AlterField(
            model_name="product",
            name="description",
            field=models.TextField(blank=True, verbose_name="Description"),
        ),
        migrations.AlterField(
            model_name="product",
            name="image",
            field=models.ImageField(
                blank=True, upload_to="product_images/", verbose_name="Main Image"
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="name",
            field=models.CharField(max_length=255, verbose_name="Name"),
        ),
        migrations.AlterField(
            model_name="product",
            name="price",
            field=models.DecimalField(
                decimal_places=2, max_digits=10, verbose_name="Price"
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="shop",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="products",
                to="shops.shop",
                verbose_name="Shop",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="stock_quantity",
            field=models.PositiveIntegerField(default=0, verbose_name="Stock Quantity"),
        ),
        migrations.AlterField(
            model_name="product",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Updated At"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["shop"], name="products_pr_shop_id_6c5838_idx"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["sku"], name="products_pr_sku_ca0cdc_idx"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["is_available"], name="products_pr_is_avai_c23034_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["discount_percentage"], name="products_pr_discoun_97bfb8_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["is_featured"], name="products_pr_is_feat_a5d7cd_idx"
            ),
        ),
    ]
