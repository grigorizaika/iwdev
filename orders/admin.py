from django.contrib import admin
from orders.models import (Order, Task)
# Register your models here.


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    pass
