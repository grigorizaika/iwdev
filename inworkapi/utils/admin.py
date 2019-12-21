from django.contrib import admin

# Register your models here.
from utils.models import Address

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    pass