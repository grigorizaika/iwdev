# Generated by Django 2.2.8 on 2020-05-05 19:43

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_auto_20200218_2219'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='date',
        ),
        migrations.AddField(
            model_name='task',
            name='starts_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 5, 5, 19, 43, 33, 578147)),
        ),
    ]
