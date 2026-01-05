"""Serializers for Response and PartialResponse."""
from rest_framework import serializers

from apps.surveys.models import Survey

from .models import PartialResponse, Response


class ResponseSerializer(serializers.ModelSerializer):
    """Serializer for survey responses."""
    
    survey_title = serializers.CharField(source="survey.title", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    
    class Meta:
        model = Response
        fields = [
            "id", "survey", "survey_title", "user", "user_email",
            "data", "submitted_at", "completion_time_seconds"
        ]
        read_only_fields = ["id", "survey_title", "user_email", "submitted_at"]


class PartialResponseSerializer(serializers.ModelSerializer):
    """Serializer for partial (in-progress) responses."""
    
    class Meta:
        model = PartialResponse
        fields = [
            "id", "survey", "session_token", "data",
            "last_section_id", "last_field_id", "started_at", "last_updated"
        ]
        read_only_fields = ["id", "started_at", "last_updated"]


class SubmissionSerializer(serializers.Serializer):
    """Serializer for final survey submission with validation."""
    
    data = serializers.JSONField()
    session_token = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validate submission against logic engine."""
        from apps.logic_engine import LogicEngine
        
        survey = self.context.get("survey")
        submitted_data = attrs.get("data", {})
        
        # Initialize logic engine with submitted data
        engine = LogicEngine(submitted_data)
        
        # Validate submission
        is_valid, errors = engine.validate_submission(survey, submitted_data)
        
        if not is_valid:
            raise serializers.ValidationError({"data": errors})
        
        return attrs
