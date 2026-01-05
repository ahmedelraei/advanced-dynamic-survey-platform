from django.contrib import admin

from .models import PartialResponse, Response


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ("survey", "user", "submitted_at", "ip_address")
    list_filter = ("survey", "submitted_at")
    search_fields = ("survey__title", "user__email")
    readonly_fields = ("id", "submitted_at", "data", "encrypted_data")
    date_hierarchy = "submitted_at"


@admin.register(PartialResponse)
class PartialResponseAdmin(admin.ModelAdmin):
    list_display = ("survey", "session_token", "user", "last_updated")
    list_filter = ("survey", "last_updated")
    search_fields = ("session_token", "user__email")
    readonly_fields = ("id", "started_at", "last_updated")
