# Generated by Django 2.2.8 on 2020-01-15 14:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='address_owner',
            field=models.OneToOneField(default=1, on_delete=django.db.models.deletion.CASCADE, to='utils.AddressOwner'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.Role'),
        ),
    ]
