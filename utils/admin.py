from django.contrib import admin

# Register your models here.
from utils.models import Address, AddressOwner, CustomFile, FileOwner


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    pass


@admin.register(AddressOwner)
class AddressOwnerAdmin(admin.ModelAdmin):
    pass
    # def has_delete_permission(self, request, obj=None):
    #     return False


@admin.register(CustomFile)
class CustomFileAdmin(admin.ModelAdmin):
    pass


@admin.register(FileOwner)
class FileOwnerAdmin(admin.ModelAdmin):
    pass
    # def has_delete_permission(self, request, obj=None):
    #     return False
