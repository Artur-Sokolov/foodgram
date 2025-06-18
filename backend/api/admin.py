from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Кастомный админ для модели User."""

    list_display = (
        'id', 'username', 'email', 'last_name', 'first_name', 'role'
    )
    list_filter = ('role',)
    search_fields = ('email', 'username')
    ordering = ('id',)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name')}),
        ('Права доступа', {'fields': (
            'role', 'is_active', 'is_staff', 'is_superuser'
        )}),
        ('Дополнительно', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )