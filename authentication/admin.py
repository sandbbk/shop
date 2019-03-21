from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from authentication.forms import (UserChangeForm, UserCreationForm)
from shop.models import User


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = [field.name for field in User._meta.fields]
    list_filter = ('is_staff',)
    fieldsets = (
        ('General', {'fields': ('email', 'password', 'phone')}),
        ('Personal info', {'fields': ('username', 'address', 'zip_code', 'birth_day', 'purse',)}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()


admin.site.register(User, UserAdmin)
