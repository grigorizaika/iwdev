# Generated by Django 2.2.8 on 2020-01-15 05:22

from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('utils', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40, unique=True)),
                ('email', models.EmailField(max_length=254, verbose_name='email address')),
                ('contact_name', models.CharField(max_length=40)),
                ('contact_phone', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None)),
                ('logo_url', models.URLField(blank=True, max_length=300, null=True)),
                ('address_owner', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='utils.AddressOwner')),
            ],
        ),
    ]
