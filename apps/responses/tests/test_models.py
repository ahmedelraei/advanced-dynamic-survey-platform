"""Unit tests for Response and PartialResponse models."""
import pytest
from django.contrib.auth import get_user_model
from conftest import create_user_with_group
from apps.users.models import SURVEY_ADMIN_GROUP, SURVEY_ANALYST_GROUP, SURVEY_VIEWER_GROUP

from apps.responses.models import PartialResponse, Response
from apps.surveys.models import Field, FieldType, Section, Survey

User = get_user_model()


@pytest.mark.django_db
class TestResponseModel:
    """Test Response model functionality."""
    
    def test_create_response(self):
        """Test creating a response."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        
        response = Response.objects.create(
            survey=survey,
            user=user,
            data={"field1": "value1", "field2": "value2"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        assert response.id is not None
        assert response.survey == survey
        assert response.user == user
        assert response.data == {"field1": "value1", "field2": "value2"}
        assert response.ip_address == "192.168.1.1"
    
    def test_create_anonymous_response(self):
        """Test creating an anonymous response."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        
        response = Response.objects.create(
            survey=survey,
            user=None,
            data={"field1": "anonymous value"}
        )
        
        assert response.user is None
        assert str(response) == "Response to Test Survey by Anonymous"
    
    def test_response_encrypted_data(self):
        """Test storing encrypted data."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        
        response = Response.objects.create(
            survey=survey,
            data={"field1": "public"},
            encrypted_data="encrypted_sensitive_data"
        )
        
        assert response.encrypted_data == "encrypted_sensitive_data"
    
    def test_response_completion_time(self):
        """Test storing completion time."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        
        response = Response.objects.create(
            survey=survey,
            data={},
            completion_time_seconds=120
        )
        
        assert response.completion_time_seconds == 120
    
    def test_response_cascade_delete(self):
        """Test responses are deleted when survey is deleted."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        response = Response.objects.create(survey=survey, data={})
        
        survey.delete()
        
        assert not Response.objects.filter(id=response.id).exists()
    
    def test_response_ordering(self):
        """Test responses are ordered by submitted_at descending."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        
        response1 = Response.objects.create(survey=survey, data={"order": 1})
        response2 = Response.objects.create(survey=survey, data={"order": 2})
        response3 = Response.objects.create(survey=survey, data={"order": 3})
        
        responses = list(Response.objects.all())
        assert responses[0] == response3
        assert responses[1] == response2
        assert responses[2] == response1


@pytest.mark.django_db
class TestPartialResponseModel:
    """Test PartialResponse model functionality."""
    
    def test_create_partial_response(self):
        """Test creating a partial response."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        
        partial = PartialResponse.objects.create(
            survey=survey,
            session_token="abc123",
            data={"field1": "partial value"}
        )
        
        assert partial.id is not None
        assert partial.survey == survey
        assert partial.session_token == "abc123"
        assert partial.data == {"field1": "partial value"}
    
    def test_partial_response_with_user(self):
        """Test partial response with authenticated user."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        
        partial = PartialResponse.objects.create(
            survey=survey,
            session_token="abc123",
            user=user,
            data={}
        )
        
        assert partial.user == user
    
    def test_partial_response_progress_tracking(self):
        """Test tracking progress with section/field IDs."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        section = Section.objects.create(survey=survey, title="Section 1")
        field = Field.objects.create(
            section=section,
            field_type=FieldType.TEXT,
            label="Name"
        )
        
        partial = PartialResponse.objects.create(
            survey=survey,
            session_token="abc123",
            data={},
            last_section_id=section.id,
            last_field_id=field.id
        )
        
        assert partial.last_section_id == section.id
        assert partial.last_field_id == field.id
    
    def test_unique_survey_session_constraint(self):
        """Test unique constraint on survey + session_token."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        
        PartialResponse.objects.create(
            survey=survey,
            session_token="abc123",
            data={}
        )
        
        # Attempting to create another with same survey + session should fail
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            PartialResponse.objects.create(
                survey=survey,
                session_token="abc123",
                data={}
            )
    
    def test_update_or_create_partial_response(self):
        """Test updating existing partial response."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        
        # Create initial
        partial1, created1 = PartialResponse.objects.update_or_create(
            survey=survey,
            session_token="abc123",
            defaults={"data": {"field1": "value1"}}
        )
        
        assert created1 is True
        assert partial1.data == {"field1": "value1"}
        
        # Update existing
        partial2, created2 = PartialResponse.objects.update_or_create(
            survey=survey,
            session_token="abc123",
            defaults={"data": {"field1": "updated", "field2": "new"}}
        )
        
        assert created2 is False
        assert partial2.id == partial1.id
        assert partial2.data == {"field1": "updated", "field2": "new"}
    
    def test_partial_response_string_representation(self):
        """Test string representation."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        
        partial = PartialResponse.objects.create(
            survey=survey,
            session_token="abc123def456",
            data={}
        )
        
        assert str(partial) == "Partial: Test Survey - abc123de..."
    
    def test_partial_response_cascade_delete(self):
        """Test partial responses are deleted when survey is deleted."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        partial = PartialResponse.objects.create(
            survey=survey,
            session_token="abc123",
            data={}
        )
        
        survey.delete()
        
        assert not PartialResponse.objects.filter(id=partial.id).exists()
