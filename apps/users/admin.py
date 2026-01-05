from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Organization, User


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "user_count")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description")
    readonly_fields = ("id", "created_at", "updated_at")
    
    def user_count(self, obj):
        return obj.users.count()
    user_count.short_description = "Users"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "username", "organization", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "groups", "organization")
    search_fields = ("email", "username", "organization__name")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Organization", {"fields": ("organization",)}),
    )
