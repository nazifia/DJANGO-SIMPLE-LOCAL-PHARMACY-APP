# Generated by Django 5.0 on 2024-06-02 21:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmapp', '0017_alter_wallet_customer'),
    ]

    operations = [
        migrations.AddField(
            model_name='sales',
            name='customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='pharmapp.customers'),
        ),
    ]
