# Generated by Django 5.1.6 on 2025-03-25 23:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_add_email_change_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='sustainability_preference',
            field=models.IntegerField(default=5),
        ),
    ]
