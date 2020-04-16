from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.forms import (CustomUserCreationForm, CustomUserChangeForm)
from users.models import User as CustomUser
from users.models import Role, Absence, Company

# admin.site.unregister(User)
# UserAdmin doesn't call get_user_model().objects.create_user
# for user creation these functions, so cognito user never gets created


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    fields = [
        'email', 'role', 'name', 'surname',
        'phone', 'supervisor', 'company',
        'cognito_id', 'profile_picture_url',
        'address_owner', 'file_owner', 'is_staff'
        ]
    fieldsets = []
    readonly_fields = ('cognito_id',)
    ordering = ('email',)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'role', 'name', 'surname', 'phone',
                'address_owner', 'is_staff', 'is_superuser',
                'password1', 'password2')
            }),
    )
    search_fields = ('email', 'name', 'surname', 'phone')
    list_display = ('email', 'name', 'surname',)
    list_filter = ('is_staff',)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    pass


@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    pass


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    pass
