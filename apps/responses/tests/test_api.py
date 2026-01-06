"""Integration tests for Response API endpoints."""
import uuid
from conftest import create_user_with_group
from apps.users.models import SURVEY_ADMIN_GROUP, SURVEY_ANALYST_GROUP, SURVEY_VIEWER_GROUP

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.responses.models import PartialResponse, Response
from apps.surveys.models import Field, FieldType, Section, Survey

User = get_user_model()


@pytest.mark.django_db
class TestPartialSaveAPI:
    """Test partial save (heartbeat) endpoint."""
    
    @pytest.fixture
    def api_client(self):
        """Create API client."""
        return APIClient()
    
    @pytest.fixture
    def survey(self):
        """Create a test survey."""
        user = create_user_with_group(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user, is_active=True)
        section = Section.objects.create(survey=survey, title="Section 1", order=0)
        Field.objects.create(
            section=section,
            field_type=FieldType.TEXT,
            label="Name",
            is_required=True,
            order=0
        )
        return survey
    
    def test_create_partial_response(self, api_client, survey):
        """Test creating a new partial response."""
        data = {
            "data": {"field1": "partial value"},
            "last_section_id": None,
            "last_field_id": None
        }
        
        response = api_client.post(
            f"/api/v1/surveys/{survey.id}/partial/",
            data,
            format="json"
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert "session_token" in response.data
        assert response.data["partial_response"]["data"] == {"field1": "partial value"}
        
        # Verify in database
        session_token = response.data["session_token"]
        partial = PartialResponse.objects.get(
            survey=survey,
            session_token=session_token
        )
        assert partial.data == {"field1": "partial value"}
    
    def test_update_existing_partial_response(self, api_client, survey):
        """Test updating an existing partial response."""
        session_token = str(uuid.uuid4())
        
        # Create initial partial
        data1 = {
            "session_token": session_token,
            "data": {"field1": "initial"}
        }
        
        response1 = api_client.post(
            f"/api/v1/surveys/{survey.id}/partial/",
            data1,
            format="json"
        )
        
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Update with more data
        data2 = {
            "session_token": session_token,
            "data": {"field1": "updated", "field2": "new"}
        }
        
        response2 = api_client.post(
            f"/api/v1/surveys/{survey.id}/partial/",
            data2,
            format="json"
        )
        
        assert response2.status_code == status.HTTP_200_OK
        assert response2.data["partial_response"]["data"] == {"field1": "updated", "field2": "new"}
        
        # Verify only one partial exists
        assert PartialResponse.objects.filter(survey=survey, session_token=session_token).count() == 1
    
    def test_retrieve_partial_response(self, api_client, survey):
        """Test retrieving an existing partial response."""
        session_token = str(uuid.uuid4())
        
        PartialResponse.objects.create(
            survey=survey,
            session_token=session_token,
            data={"field1": "saved value"}
        )
        
        response = api_client.get(
            f"/api/v1/surveys/{survey.id}/partial/?session_token={session_token}"
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"] == {"field1": "saved value"}
    
    def test_retrieve_partial_response_not_found(self, api_client, survey):
        """Test retrieving non-existent partial response."""
        response = api_client.get(
            f"/api/v1/surveys/{survey.id}/partial/?session_token=nonexistent"
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_partial_save_inactive_survey(self, api_client):
        """Test partial save fails for inactive survey."""
        user = create_user_with_group(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Inactive Survey", owner=user, is_active=False)
        
        data = {"data": {"field1": "value"}}
        
        response = api_client.post(
            f"/api/v1/surveys/{survey.id}/partial/",
            data,
            format="json"
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestSubmitAPI:
    """Test survey submission endpoint."""
    
    @pytest.fixture
    def api_client(self):
        """Create API client."""
        return APIClient()
    
    @pytest.fixture
    def survey(self):
        """Create a test survey with fields."""
        user = create_user_with_group(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user, is_active=True)
        section = Section.objects.create(survey=survey, title="Section 1", order=0)
        
        # Required text field
        Field.objects.create(
            section=section,
            field_type=FieldType.TEXT,
            label="Name",
            is_required=True,
            order=0
        )
        
        # Optional email field (sensitive)
        Field.objects.create(
            section=section,
            field_type=FieldType.EMAIL,
            label="Email",
            is_required=False,
            is_sensitive=True,
            order=1
        )
        
        return survey
    
    def test_submit_valid_response(self, api_client, survey):
        """Test submitting a valid survey response."""
        section = survey.sections.first()
        name_field = section.fields.get(order=0)
        email_field = section.fields.get(order=1)
        
        data = {
            "data": {
                str(name_field.id): "John Doe",
                str(email_field.id): "john@example.com"
            }
        }
        
        response = api_client.post(
            f"/api/v1/surveys/{survey.id}/submit/",
            data,
            format="json"
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.data
        assert response.data["message"] == "Survey submitted successfully"
        
        # Verify in database
        survey_response = Response.objects.get(id=response.data["id"])
        assert survey_response.data[str(name_field.id)] == "John Doe"
        assert survey_response.data[str(email_field.id)] == "john@example.com"
    
    def test_submit_missing_required_field(self, api_client, survey):
        """Test submission fails when required field is missing."""
        section = survey.sections.first()
        email_field = section.fields.get(order=1)
        
        data = {
            "data": {
                str(email_field.id): "john@example.com"
                # Missing required name field
            }
        }
        
        response = api_client.post(
            f"/api/v1/surveys/{survey.id}/submit/",
            data,
            format="json"
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_submit_cleans_up_partial_response(self, api_client, survey):
        """Test submission deletes associated partial response."""
        session_token = str(uuid.uuid4())
        
        # Create partial response
        PartialResponse.objects.create(
            survey=survey,
            session_token=session_token,
            data={"field1": "partial"}
        )
        
        section = survey.sections.first()
        name_field = section.fields.get(order=0)
        
        data = {
            "session_token": session_token,
            "data": {
                str(name_field.id): "John Doe"
            }
        }
        
        response = api_client.post(
            f"/api/v1/surveys/{survey.id}/submit/",
            data,
            format="json"
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify partial response was deleted
        assert not PartialResponse.objects.filter(
            survey=survey,
            session_token=session_token
        ).exists()
    
    def test_submit_inactive_survey(self, api_client):
        """Test submission fails for inactive survey."""
        user = create_user_with_group(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Inactive Survey", owner=user, is_active=False)
        
        data = {"data": {}}
        
        response = api_client.post(
            f"/api/v1/surveys/{survey.id}/submit/",
            data,
            format="json"
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_submit_anonymous_response(self, api_client, survey):
        """Test anonymous user can submit response."""
        section = survey.sections.first()
        name_field = section.fields.get(order=0)
        
        data = {
            "data": {
                str(name_field.id): "Anonymous User"
            }
        }
        
        response = api_client.post(
            f"/api/v1/surveys/{survey.id}/submit/",
            data,
            format="json"
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        
        survey_response = Response.objects.get(id=response.data["id"])
        assert survey_response.user is None


@pytest.mark.django_db
class TestResponseViewSetAPI:
    """Test Response viewing endpoints."""
    
    @pytest.fixture
    def api_client(self):
        """Create API client."""
        return APIClient()
    
    @pytest.fixture
    def admin_user(self):
        """Create admin user."""
        return create_user_with_group(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
    
    @pytest.fixture
    def survey(self, admin_user):
        """Create a test survey."""
        return Survey.objects.create(title="Test Survey", owner=admin_user, is_active=True)
    
    def test_list_responses(self, api_client, admin_user, survey):
        """Test listing responses for a survey."""
        api_client.force_authenticate(user=admin_user)
        
        Response.objects.create(survey=survey, data={"field1": "value1"})
        Response.objects.create(survey=survey, data={"field1": "value2"})
        
        response = api_client.get(f"/api/v1/surveys/{survey.id}/responses/")
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2
    
    def test_retrieve_response(self, api_client, admin_user, survey):
        """Test retrieving a specific response."""
        api_client.force_authenticate(user=admin_user)
        
        survey_response = Response.objects.create(
            survey=survey,
            data={"field1": "value1"}
        )
        
        response = api_client.get(
            f"/api/v1/surveys/{survey.id}/responses/{survey_response.id}/"
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"] == {"field1": "value1"}
    
    def test_list_responses_unauthenticated(self, api_client, survey):
        """Test listing responses without authentication fails."""
        response = api_client.get(f"/api/v1/surveys/{survey.id}/responses/")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_export_responses(self, api_client, admin_user, survey):
        """Test triggering CSV export."""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.post(f"/api/v1/surveys/{survey.id}/responses/export/")
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert "Export started" in response.data["message"]
