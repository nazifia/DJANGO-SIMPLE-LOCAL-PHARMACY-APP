# Generated by Django 5.0 on 2024-05-26 11:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmapp', '0003_sales_name_sales_quantity_alter_sales_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sales',
            name='name',
        ),
        migrations.RemoveField(
            model_name='sales',
            name='quantity',
        ),
        migrations.AlterField(
            model_name='sales',
            name='date',
            field=models.DateField(auto_now_add=True),
        ),
    ]
