# Generated by Django 5.2.2 on 2025-06-20 15:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0008_remove_product_price_productvariant_cartitem_variant_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productvariant',
            name='ram',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
