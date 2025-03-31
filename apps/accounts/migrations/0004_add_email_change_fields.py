# Generated by Django 5.1.6 on 2025-03-24 23:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_alter_user_managers"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="email_change_token",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="email_token_created_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="new_email",
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
