"""
AuditLog model for compliance tracking.
Maps to Security & Compliance: Audit Trail requirement.
"""
import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class AuditAction(models.TextChoices):
    """Types of auditable actions."""
    CREATE = "create", "Create"
    READ = "read", "Read"
    UPDATE = "update", "Update"
    DELETE = "delete", "Delete"
    LOGIN = "login", "Login"
    LOGOUT = "logout", "Logout"
    EXPORT = "export", "Export"
    PII_ACCESS = "pii_access", "PII Access"


class AuditLog(models.Model):
    """
    Immutable audit log for tracking RBAC actions and edits.
    Every API hit that modifies a survey or accesses PII is logged.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Action details
    action = models.CharField(max_length=20, choices=AuditAction.choices)
    description = models.TextField(blank=True)
    
    # Actor
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs"
    )
    
    # Target object (generic relation)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    object_id = models.CharField(max_length=255, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    
    # Change tracking (JSONB)
    # Structure: {"field": {"old": "value", "new": "value"}}
    changes = models.JSONField(default=dict, blank=True)
    
    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    
    # Timestamp (immutable)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "audit_logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["action"]),
            models.Index(fields=["timestamp"]),
            models.Index(fields=["content_type", "object_id"]),
        ]
        # Make table effectively append-only at application level
        # (true immutability requires DB-level triggers)
    
    def __str__(self):
        return f"{self.action} by {self.user} at {self.timestamp}"
    
    def save(self, *args, **kwargs):
        """Prevent updates to existing audit logs."""
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise ValueError("Audit logs are immutable and cannot be updated")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of audit logs."""
        raise ValueError("Audit logs are immutable and cannot be deleted")
