# Generated by Django 2.2.8 on 2019-12-22 04:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20191222_0406'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='firebaseId',
            field=models.CharField(max_length=191, unique=True),
        ),
    ]
