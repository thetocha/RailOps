from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):  # type: ignore[type-arg]
    list_display = ("username", "email", "is_active", "is_staff", "created_at")
    list_filter = ("is_active", "is_staff", "groups")
    readonly_fields = (*DjangoUserAdmin.readonly_fields, "created_at", "updated_at")
    ordering = ("username",)
