# Generated by Django 2.2.8 on 2020-01-18 14:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=40)),
                ('billing_period', models.PositiveIntegerField()),
                ('status', models.CharField(default='', max_length=40)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=40)),
                ('date', models.DateField()),
                ('manual_time_set', models.BooleanField()),
                ('hours_worked', models.TimeField(blank=True, null=True)),
                ('is_hours_worked_accepted', models.BooleanField(blank=True, default=False, null=True)),
                ('is_cancelled', models.BooleanField(blank=True, default=False, null=True)),
                ('description', models.TextField(blank=True)),
                ('comment', models.TextField(blank=True)),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='orders.Order')),
            ],
        ),
    ]
