# Generated by Django 5.0.7 on 2024-11-06 20:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0005_remove_product_variations_product_discount_price'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='is_anonymous_user',
        ),
    ]