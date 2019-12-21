# Generated by Django 2.2.8 on 2019-12-21 00:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_auto_20191221_0027'),
    ]

    operations = [
        migrations.AlterField(
            model_name='role',
            name='name',
            field=models.CharField(choices=[('Administrator', 'administrator'), ('Coordinator', 'coordinator'), ('Worker', 'worker')], max_length=13, unique=True),
        ),
    ]
