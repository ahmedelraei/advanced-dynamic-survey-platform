"""
Audit logging middleware for automatic API tracking.
"""
from django.contrib.contenttypes.models import ContentType

from .models import AuditAction, AuditLog


class AuditLogMiddleware:
    """
    Middleware to automatically log API requests that modify data.
    Tracks: POST, PUT, PATCH, DELETE on /api/ endpoints.
    """
    
    AUDITABLE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    AUDITABLE_PATHS = ["/api/"]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Only audit specific methods on API paths
        if (
            request.method in self.AUDITABLE_METHODS
            and any(request.path.startswith(p) for p in self.AUDITABLE_PATHS)
            and response.status_code < 400  # Only successful requests
        ):
            self._create_audit_log(request, response)
        
        return response
    
    def _create_audit_log(self, request, response):
        """Create an audit log entry for the request."""
        action_map = {
            "POST": AuditAction.CREATE,
            "PUT": AuditAction.UPDATE,
            "PATCH": AuditAction.UPDATE,
            "DELETE": AuditAction.DELETE,
        }
        
        try:
            AuditLog.objects.create(
                action=action_map.get(request.method, AuditAction.UPDATE),
                user=request.user if request.user.is_authenticated else None,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
                request_path=request.path[:500],
                request_method=request.method,
            )
        except Exception:
            # Don't let audit logging break the request
            pass
    
    def _get_client_ip(self, request):
        """Extract client IP from request headers."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")


def log_audit_event(
    action: str,
    user=None,
    obj=None,
    changes: dict = None,
    description: str = "",
    request=None,
):
    """
    Utility function to create audit log entries programmatically.
    Use this for custom audit events not captured by middleware.
    """
    content_type = None
    object_id = ""
    
    if obj:
        content_type = ContentType.objects.get_for_model(obj)
        object_id = str(obj.pk)
    
    ip_address = None
    user_agent = ""
    request_path = ""
    request_method = ""
    
    if request:
        ip_address = (
            request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
            or request.META.get("REMOTE_ADDR")
        )
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]
        request_path = request.path[:500]
        request_method = request.method
    
    return AuditLog.objects.create(
        action=action,
        user=user,
        content_type=content_type,
        object_id=object_id,
        changes=changes or {},
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        request_path=request_path,
        request_method=request_method,
    )
