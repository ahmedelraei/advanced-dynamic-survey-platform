"""
Response and PartialResponse models for ADSP.
Maps to FR 2.1, FR 2.2: Real-time Validation and Partial Saves.
"""
import uuid

from django.conf import settings
from django.db import models


class Response(models.Model):
    """
    Stores final survey submissions.
    Data is stored as JSONB with encrypted sensitive fields.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey = models.ForeignKey(
        "surveys.Survey",
        on_delete=models.CASCADE,
        related_name="responses"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="survey_responses"
    )
    
    # Response data (JSONB)
    # Structure: {"field_uuid": "value", "field_uuid2": ["multi", "values"]}
    data = models.JSONField(default=dict)
    
    # Encrypted storage for sensitive field values
    # TODO: Add encryption in production
    encrypted_data = models.TextField(blank=True, default="")
    
    # Submission metadata
    submitted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    
    # Completion tracking
    completion_time_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        db_table = "responses"
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(fields=["survey"]),
            models.Index(fields=["user"]),
            models.Index(fields=["survey", "user"]),
            models.Index(fields=["submitted_at"]),
        ]
    
    def __str__(self):
        return f"Response to {self.survey.title} by {self.user or 'Anonymous'}"


class PartialResponse(models.Model):
    """
    Stores in-progress survey submissions for auto-save/heartbeat.
    Maps to FR 2.2: Partial Saves (Heartbeat).
    Indexed by session_token for anonymous users.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey = models.ForeignKey(
        "surveys.Survey",
        on_delete=models.CASCADE,
        related_name="partial_responses"
    )
    
    # Session token for anonymous identification
    session_token = models.CharField(max_length=255, db_index=True)
    
    # Optional user linkage
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="partial_survey_responses"
    )
    
    # Partial data (JSONB)
    data = models.JSONField(default=dict)
    
    # Current section/field progress
    last_section_id = models.UUIDField(null=True, blank=True)
    last_field_id = models.UUIDField(null=True, blank=True)
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "partial_responses"
        ordering = ["-last_updated"]
        indexes = [
            models.Index(fields=["survey", "session_token"]),
            models.Index(fields=["session_token"]),
            models.Index(fields=["last_updated"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["survey", "session_token"],
                name="unique_survey_session"
            )
        ]
    
    def __str__(self):
        return f"Partial: {self.survey.title} - {self.session_token[:8]}..."
