from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Lets the site owner set a user's role (Admin / Agent / Client)."""

    fieldsets = UserAdmin.fieldsets + (
        ('Toronto Estates', {'fields': ('role', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Toronto Estates', {'fields': ('role', 'phone')}),
    )
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = UserAdmin.list_filter + ('role',)
