from django.contrib             import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin  import UserAdmin

from users.forms    import (CustomUserCreationForm, CustomUserChangeForm)
from users.models   import User as CustomUser
from users.models   import (Role, Absence)

# Register your models here.
# admin.site.unregister(User)


# Users get created just fine while using get_user_model().objects.create_user,
# but apparently admin doesn't call these functions, so that a firebase user never gets created

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    fields = ['email', 'role', 'name', 'surname', 'phone', 'address_owner', 'supervisor', 'is_staff', 'cognito_sub']
    #fields = '__all__'
    fieldsets =  []
    ordering = ('email',)
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'role', 'name', 'surname', 'phone', 
                'address_owner', 'is_staff', 'is_superuser', 'password1', 'password2'
                )
            }
        ),
    )
    search_fields = ('email', 'name', 'surname', 'phone')
    list_display = ('email', 'name', 'surname',)
    list_filter = ('is_staff',)

    readonly_fields=('cognito_sub', )
    cognito_sub = lambda self, instance: instance.get_cognito_sub()
    cognito_sub.short_description = 'Cognito sub'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    pass

@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    pass