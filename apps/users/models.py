"""
Custom User Model for ADSP.
"""
import uuid

from django.contrib.auth.models import AbstractUser, Group
from django.db import models


class Organization(models.Model):
    """Organization model for multi-tenant support."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "organizations"
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        ordering = ["name"]
    
    def __str__(self):
        return self.name


class User(AbstractUser):
    """Extended user model with organization relationship."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
        blank=True,
        help_text="Organization this user belongs to"
    )
    
    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
    
    def __str__(self):
        return self.email or self.username


# RBAC Groups - created via migrations or management command
SURVEY_ADMIN_GROUP = "survey_admins"
SURVEY_ANALYST_GROUP = "survey_analysts"
SURVEY_VIEWER_GROUP = "survey_viewers"


def create_rbac_groups():
    """Create default RBAC groups if they don't exist."""
    groups = [SURVEY_ADMIN_GROUP, SURVEY_ANALYST_GROUP, SURVEY_VIEWER_GROUP]
    for group_name in groups:
        Group.objects.get_or_create(name=group_name)
