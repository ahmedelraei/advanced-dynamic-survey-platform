"""
Survey, Section, and Field models for ADSP.
"""
import uuid

from django.conf import settings
from django.db import models


class Survey(models.Model):
    """
    High-level survey container with versioning support.
    Maps to FR 1.1: Survey > Section > Field hierarchy.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="surveys"
    )
    is_active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "surveys"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["created_at"]),
        ]
    
    def __str__(self):
        return f"{self.title} (v{self.version})"


class Section(models.Model):
    """
    Groups fields within a survey and holds conditional visibility logic.
    Maps to FR 1.2: Conditional Logic Engine.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name="sections"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    
    # Conditional visibility rules (JSONB)
    # Example: {"conditions": [{"field_id": "uuid", "operator": "equals", "value": "USA"}], "action": "show"}
    logic_rules = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "sections"
        ordering = ["survey", "order"]
        indexes = [
            models.Index(fields=["survey", "order"]),
        ]
    
    def __str__(self):
        return f"{self.survey.title} - {self.title}"


class FieldType(models.TextChoices):
    """Supported field types for survey questions."""
    TEXT = "text", "Text"
    TEXTAREA = "textarea", "Text Area"
    NUMBER = "number", "Number"
    EMAIL = "email", "Email"
    PHONE = "phone", "Phone"
    DATE = "date", "Date"
    DATETIME = "datetime", "Date & Time"
    SELECT = "select", "Dropdown"
    MULTISELECT = "multiselect", "Multi-Select"
    RADIO = "radio", "Radio Buttons"
    CHECKBOX = "checkbox", "Checkbox"
    RATING = "rating", "Rating Scale"
    FILE = "file", "File Upload"


class Field(models.Model):
    """
    Individual question/input within a section.
    Supports conditional visibility, validation, and PII encryption.
    Maps to FR 1.3: Cross-Section Dependencies and FR 2.3: Data Encryption.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="fields"
    )
    
    # Field configuration
    field_type = models.CharField(max_length=20, choices=FieldType.choices)
    label = models.CharField(max_length=500)
    placeholder = models.CharField(max_length=255, blank=True)
    help_text = models.TextField(blank=True)
    
    # Options for select/radio/checkbox types (JSONB)
    # Example: [{"value": "usa", "label": "USA"}, {"value": "uk", "label": "UK"}]
    options = models.JSONField(default=list, blank=True)
    
    # Validation
    is_required = models.BooleanField(default=False)
    validation_regex = models.CharField(max_length=500, blank=True)
    validation_message = models.CharField(max_length=255, blank=True)
    min_value = models.IntegerField(null=True, blank=True)
    max_value = models.IntegerField(null=True, blank=True)
    
    # Conditional visibility (field-level)
    logic_rules = models.JSONField(default=dict, blank=True)
    
    # Cross-section dependencies
    # Example: {"depends_on": "field_uuid", "filter_by": "country"}
    dependency_config = models.JSONField(default=dict, blank=True)
    
    # Security - marks field as containing PII
    is_sensitive = models.BooleanField(default=False)
    
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "fields"
        ordering = ["section", "order"]
        indexes = [
            models.Index(fields=["section", "order"]),
            models.Index(fields=["field_type"]),
        ]
    
    def __str__(self):
        return f"{self.section.title} - {self.label}"
