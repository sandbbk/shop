# Generated by Django 2.1.7 on 2019-02-25 10:56

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
                ('icon', models.ImageField(help_text='jpg/png - file', upload_to='', verbose_name='Photo')),
                ('description', models.TextField(blank=True, max_length=512, null=True)),
                ('parent', models.ForeignKey(blank=True, max_length=64, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subcategory', to='shop.Category', verbose_name='Parent')),
            ],
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('full_name', models.CharField(db_index=True, max_length=128)),
                ('email', models.EmailField(db_index=True, max_length=64, unique=True)),
                ('phone', models.CharField(db_index=True, max_length=13, unique=True)),
                ('address', models.CharField(blank=True, max_length=256, null=True)),
                ('zip_code', models.SmallIntegerField()),
                ('birth_day', models.DateField(default=None, null=True)),
                ('purse', models.DecimalField(decimal_places=2, default=0, max_digits=7)),
                ('cart', django.contrib.postgres.fields.jsonb.JSONField(default=None)),
                ('pwd', models.CharField(max_length=64)),
                ('is_modered', models.CharField(choices=[('false', 'false'), ('true', 'true')], default='false', max_length=5)),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('products', django.contrib.postgres.fields.jsonb.JSONField(default=None)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='shop.Customer')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('code', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=64)),
                ('price', models.DecimalField(decimal_places=2, max_digits=7)),
                ('discount', models.FloatField(default=0)),
                ('qu_in_stock', models.IntegerField(db_index=True, default=0)),
                ('photo', models.ImageField(blank=True, help_text='jpg/png - file', upload_to='', verbose_name='Photo')),
                ('short_description', models.CharField(max_length=256)),
                ('description', models.TextField(blank=True, max_length=512, null=True)),
                ('date_of_come', models.DateTimeField(default=None)),
                ('category', models.ForeignKey(max_length=64, on_delete=django.db.models.deletion.CASCADE, related_name='Products', to='shop.Category', verbose_name='Category')),
            ],
        ),
    ]
