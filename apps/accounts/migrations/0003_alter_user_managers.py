# Generated by Django 5.1.6 on 2025-03-04 17:47

import apps.accounts.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_user_managers_remove_user_username_and_more'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='user',
            managers=[
                ('objects', apps.accounts.models.UserManager()),
            ],
        ),
    ]
