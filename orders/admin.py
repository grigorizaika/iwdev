from django.contrib import admin
from orders.models import (Order, Task)
# Register your models here.


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'name', 'starts_at',
                    'worker', 'manual_time_set', 'hours_worked',
                    'is_hours_worked_accepted')
    list_filter = ('order', 'order__client',
                   'starts_at', 'worker')
