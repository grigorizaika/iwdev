from django.contrib import admin
from clients.models import Client

# Register your models here.
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    readonly_fields = ['logo_url']
    pass
