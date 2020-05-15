from django.contrib import admin
from orders.models import (Order, Task)
# Register your models here.
from rangefilter.filter import DateRangeFilter

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'order', 'starts_at',
                    'worker', 'manual_time_set', 'hours_worked',
                    'is_hours_worked_accepted')
    list_display_links = ('id', 'name')
    list_filter = (('starts_at', DateRangeFilter), 'worker',
                   'order', 'order__client')
