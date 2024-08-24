# Generated by Django 5.0.7 on 2024-08-08 21:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0003_alter_item_barcode_alter_item_name_alter_item_price_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='item',
            old_name='price',
            new_name='buy_price',
        ),
        migrations.AddField(
            model_name='item',
            name='sell_price',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
    ]
