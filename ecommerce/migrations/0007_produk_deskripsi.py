# Generated by Django 5.2.2 on 2025-06-06 08:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0006_produk_slug_gambarproduk'),
    ]

    operations = [
        migrations.AddField(
            model_name='produk',
            name='deskripsi',
            field=models.TextField(blank=True, null=True),
        ),
    ]
