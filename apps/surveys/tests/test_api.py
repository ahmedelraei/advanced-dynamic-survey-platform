"""Integration tests for Survey API endpoints."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from conftest import create_user_with_group
from apps.users.models import SURVEY_ADMIN_GROUP, SURVEY_ANALYST_GROUP, SURVEY_VIEWER_GROUP

from apps.surveys.models import Field, FieldType, Section, Survey

User = get_user_model()


@pytest.mark.django_db
class TestSurveyAPI:
    """Test Survey API endpoints."""
    
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
    def analyst_user(self):
        """Create analyst user."""
        return create_user_with_group(
            username="analyst",
            email="analyst@example.com",
            password="analystpass123",
            group_name=SURVEY_ANALYST_GROUP
        )
    
    @pytest.fixture
    def viewer_user(self):
        """Create viewer user."""
        return create_user_with_group(
            username="viewer",
            email="viewer@example.com",
            password="viewerpass123",
            group_name=SURVEY_VIEWER_GROUP
        )
    
    def test_list_surveys_authenticated(self, api_client, admin_user):
        """Test listing surveys as authenticated user."""
        api_client.force_authenticate(user=admin_user)
        
        Survey.objects.create(title="Survey 1", owner=admin_user)
        Survey.objects.create(title="Survey 2", owner=admin_user)
        
        response = api_client.get("/api/v1/surveys/")
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2
    
    def test_list_surveys_unauthenticated(self, api_client):
        """Test listing surveys without authentication fails."""
        response = api_client.get("/api/v1/surveys/")
        
        # DRF returns 403 Forbidden when using IsAuthenticated permission
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_survey_as_admin(self, api_client, admin_user):
        """Test creating a survey as admin."""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            "title": "New Survey",
            "description": "Test survey",
            "is_active": True,
            "sections": [
                {
                    "title": "Section 1",
                    "fields": [
                        {
                            "field_type": "text",
                            "label": "Name",
                            "is_required": True
                        }
                    ]
                }
            ]
        }
        
        response = api_client.post("/api/v1/surveys/", data, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "New Survey"
        assert Survey.objects.filter(title="New Survey").exists()
    
    def test_create_survey_as_viewer_forbidden(self, api_client, viewer_user):
        """Test viewers cannot create surveys."""
        api_client.force_authenticate(user=viewer_user)
        
        data = {
            "title": "New Survey",
            "description": "Test survey",
            "is_active": True
        }
        
        response = api_client.post("/api/v1/surveys/", data, format="json")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_retrieve_survey(self, api_client, admin_user):
        """Test retrieving a specific survey."""
        api_client.force_authenticate(user=admin_user)
        
        survey = Survey.objects.create(title="Test Survey", owner=admin_user)
        section = Section.objects.create(survey=survey, title="Section 1")
        Field.objects.create(
            section=section,
            field_type=FieldType.TEXT,
            label="Name"
        )
        
        response = api_client.get(f"/api/v1/surveys/{survey.id}/")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Test Survey"
        assert len(response.data["sections"]) == 1
        assert len(response.data["sections"][0]["fields"]) == 1
    
    def test_update_survey(self, api_client, admin_user):
        """Test updating a survey."""
        api_client.force_authenticate(user=admin_user)
        
        survey = Survey.objects.create(title="Old Title", owner=admin_user)
        
        data = {
            "title": "Updated Title",
            "description": "Updated description",
            "is_active": False
        }
        
        response = api_client.patch(f"/api/v1/surveys/{survey.id}/", data, format="json")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Updated Title"
        
        survey.refresh_from_db()
        assert survey.title == "Updated Title"
        assert survey.is_active is False
    
    def test_soft_delete_survey(self, api_client, admin_user):
        """Test soft deleting a survey."""
        api_client.force_authenticate(user=admin_user)
        
        survey = Survey.objects.create(title="Test Survey", owner=admin_user, is_active=True)
        
        response = api_client.delete(f"/api/v1/surveys/{survey.id}/")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        survey.refresh_from_db()
        assert survey.is_active is False  # Soft delete
        assert Survey.objects.filter(id=survey.id).exists()  # Still in DB
    
    def test_duplicate_survey(self, api_client, admin_user):
        """Test duplicating a survey."""
        api_client.force_authenticate(user=admin_user)
        
        survey = Survey.objects.create(title="Original Survey", owner=admin_user)
        section = Section.objects.create(survey=survey, title="Section 1")
        Field.objects.create(
            section=section,
            field_type=FieldType.TEXT,
            label="Name",
            is_required=True
        )
        
        response = api_client.post(f"/api/v1/surveys/{survey.id}/duplicate/")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "Original Survey (Copy)"
        assert response.data["is_active"] is False
        
        # Verify duplication
        assert Survey.objects.count() == 2
        new_survey = Survey.objects.get(title="Original Survey (Copy)")
        assert new_survey.sections.count() == 1
        assert new_survey.sections.first().fields.count() == 1
    
    @pytest.mark.skip(reason="Object-level permissions not yet implemented")
    def test_cannot_update_other_users_survey(self, api_client, admin_user):
        """Test users cannot update surveys they don't own."""
        other_user = create_user_with_group(
            username="other",
            email="other@example.com",
            password="otherpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Other's Survey", owner=other_user)
        
        api_client.force_authenticate(user=admin_user)
        
        data = {"title": "Hacked Title"}
        response = api_client.patch(f"/api/v1/surveys/{survey.id}/", data, format="json")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestSectionAPI:
    """Test Section API endpoints."""
    
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
        return Survey.objects.create(title="Test Survey", owner=admin_user)
    
    def test_create_section(self, api_client, admin_user, survey):
        """Test creating a section."""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            "title": "New Section",
            "description": "Section description",
            "order": 0,
            "fields": [
                {
                    "field_type": "text",
                    "label": "Question 1",
                    "is_required": True
                }
            ]
        }
        
        response = api_client.post(
            f"/api/v1/surveys/{survey.id}/sections/",
            data,
            format="json"
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "New Section"
        assert Section.objects.filter(survey=survey, title="New Section").exists()
    
    def test_list_sections(self, api_client, admin_user, survey):
        """Test listing sections for a survey."""
        api_client.force_authenticate(user=admin_user)
        
        Section.objects.create(survey=survey, title="Section 1", order=0)
        Section.objects.create(survey=survey, title="Section 2", order=1)
        
        response = api_client.get(f"/api/v1/surveys/{survey.id}/sections/")
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2
    
    def test_update_section(self, api_client, admin_user, survey):
        """Test updating a section."""
        api_client.force_authenticate(user=admin_user)
        
        section = Section.objects.create(survey=survey, title="Old Title", order=0)
        
        data = {"title": "Updated Title"}
        response = api_client.patch(
            f"/api/v1/surveys/{survey.id}/sections/{section.id}/",
            data,
            format="json"
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Updated Title"
    
    def test_delete_section(self, api_client, admin_user, survey):
        """Test deleting a section."""
        api_client.force_authenticate(user=admin_user)
        
        section = Section.objects.create(survey=survey, title="Section to Delete", order=0)
        
        response = api_client.delete(f"/api/v1/surveys/{survey.id}/sections/{section.id}/")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Section.objects.filter(id=section.id).exists()


@pytest.mark.django_db
class TestPublicSurveyAPI:
    """Test public survey endpoint."""
    
    @pytest.fixture
    def api_client(self):
        """Create API client."""
        return APIClient()
    
    def test_get_active_survey_public(self, api_client):
        """Test retrieving an active survey without authentication."""
        user = create_user_with_group(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(
            title="Public Survey",
            owner=user,
            is_active=True
        )
        section = Section.objects.create(survey=survey, title="Section 1")
        Field.objects.create(section=section, field_type=FieldType.TEXT, label="Name")
        
        response = api_client.get(f"/api/v1/public/surveys/{survey.id}/")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Public Survey"
        assert len(response.data["sections"]) == 1
    
    def test_get_inactive_survey_public_fails(self, api_client):
        """Test retrieving an inactive survey fails."""
        user = create_user_with_group(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(
            title="Inactive Survey",
            owner=user,
            is_active=False
        )
        
        response = api_client.get(f"/api/v1/public/surveys/{survey.id}/")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_nonexistent_survey_public(self, api_client):
        """Test retrieving a non-existent survey."""
        import uuid
        fake_id = uuid.uuid4()
        
        response = api_client.get(f"/api/v1/public/surveys/{fake_id}/")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
