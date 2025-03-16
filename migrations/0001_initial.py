# Generated by Django 5.1.1 on 2025-03-16 18:46

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(max_length=3)),
                ('status', models.CharField(max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('transaction_amount', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('payment_method_id', models.CharField(max_length=50, null=True)),
                ('payment_type_id', models.CharField(max_length=50, null=True)),
                ('description', models.TextField(null=True)),
                ('payer_email', models.EmailField(max_length=254, null=True)),
                ('installments', models.IntegerField(null=True)),
                ('card_first_six_digits', models.CharField(max_length=6, null=True)),
                ('card_last_four_digits', models.CharField(max_length=4, null=True)),
                ('authorization_code', models.CharField(max_length=50, null=True)),
                ('transaction_details', models.JSONField(null=True)),
                ('additional_info', models.JSONField(null=True)),
                ('fees', models.JSONField(null=True)),
                ('notification_url', models.URLField(null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
