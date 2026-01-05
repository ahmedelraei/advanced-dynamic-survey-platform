from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "user", "content_type", "object_id", "timestamp", "ip_address")
    list_filter = ("action", "timestamp", "content_type")
    search_fields = ("user__email", "object_id", "description")
    readonly_fields = (
        "id", "action", "user", "content_type", "object_id",
        "changes", "ip_address", "user_agent", "request_path",
        "request_method", "timestamp", "description"
    )
    date_hierarchy = "timestamp"
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
