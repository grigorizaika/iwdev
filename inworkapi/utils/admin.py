from django.contrib import admin

# Register your models here.
from utils.models import (Address, AddressOwner)

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    pass

@admin.register(AddressOwner)
class AddressOwnerAdmin(admin.ModelAdmin):
    pass