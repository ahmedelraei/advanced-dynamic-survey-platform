"""Unit tests for Survey serializers."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from conftest import create_user_with_group
from apps.users.models import SURVEY_ADMIN_GROUP, SURVEY_ANALYST_GROUP, SURVEY_VIEWER_GROUP

from apps.surveys.models import Field, FieldType, Section, Survey
from apps.surveys.serializers import (
    FieldSerializer,
    SectionCreateSerializer,
    SectionSerializer,
    SurveyCreateSerializer,
    SurveyDetailSerializer,
    SurveyListSerializer,
)

User = get_user_model()


@pytest.mark.django_db
class TestFieldSerializer:
    """Test FieldSerializer."""
    
    def test_serialize_field(self):
        """Test serializing a field."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        section = Section.objects.create(survey=survey, title="Test Section")
        field = Field.objects.create(
            section=section,
            field_type=FieldType.TEXT,
            label="Full Name",
            placeholder="Enter your name",
            is_required=True,
            order=0
        )
        
        serializer = FieldSerializer(field)
        data = serializer.data
        
        assert data["label"] == "Full Name"
        assert data["field_type"] == "text"
        assert data["is_required"] is True
        assert data["placeholder"] == "Enter your name"
    
    def test_deserialize_field(self):
        """Test deserializing field data."""
        data = {
            "field_type": "email",
            "label": "Email Address",
            "placeholder": "you@example.com",
            "is_required": True,
            "is_sensitive": True,
            "order": 0
        }
        
        serializer = FieldSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["field_type"] == "email"
        assert serializer.validated_data["is_sensitive"] is True


@pytest.mark.django_db
class TestSectionSerializer:
    """Test SectionSerializer."""
    
    def test_serialize_section_with_fields(self):
        """Test serializing a section with nested fields."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        section = Section.objects.create(
            survey=survey,
            title="Personal Info",
            description="Your details",
            order=0
        )
        Field.objects.create(
            section=section,
            field_type=FieldType.TEXT,
            label="Name",
            order=0
        )
        Field.objects.create(
            section=section,
            field_type=FieldType.EMAIL,
            label="Email",
            order=1
        )
        
        serializer = SectionSerializer(section)
        data = serializer.data
        
        assert data["title"] == "Personal Info"
        assert data["description"] == "Your details"
        assert len(data["fields"]) == 2
        assert data["fields"][0]["label"] == "Name"
        assert data["fields"][1]["label"] == "Email"


@pytest.mark.django_db
class TestSurveyListSerializer:
    """Test SurveyListSerializer."""
    
    def test_serialize_survey_list(self):
        """Test serializing survey for list view."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(
            title="Test Survey",
            description="Test Description",
            owner=user,
            is_active=True
        )
        Section.objects.create(survey=survey, title="Section 1")
        Section.objects.create(survey=survey, title="Section 2")
        
        serializer = SurveyListSerializer(survey)
        data = serializer.data
        
        assert data["title"] == "Test Survey"
        assert data["owner_email"] == "test@example.com"
        assert data["section_count"] == 2
        assert data["is_active"] is True
        assert "sections" not in data  # List view doesn't include sections


@pytest.mark.django_db
class TestSurveyDetailSerializer:
    """Test SurveyDetailSerializer."""
    
    def test_serialize_survey_detail(self):
        """Test serializing full survey with sections and fields."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        section = Section.objects.create(survey=survey, title="Section 1", order=0)
        Field.objects.create(
            section=section,
            field_type=FieldType.TEXT,
            label="Name",
            order=0
        )
        
        serializer = SurveyDetailSerializer(survey)
        data = serializer.data
        
        assert data["title"] == "Test Survey"
        assert data["owner_email"] == "test@example.com"
        assert len(data["sections"]) == 1
        assert data["sections"][0]["title"] == "Section 1"
        assert len(data["sections"][0]["fields"]) == 1


@pytest.mark.django_db
class TestSurveyCreateSerializer:
    """Test SurveyCreateSerializer."""
    
    def test_create_survey_with_sections_and_fields(self):
        """Test creating a complete survey with nested data."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        
        factory = APIRequestFactory()
        request = factory.post("/api/v1/surveys/")
        request.user = user
        
        data = {
            "title": "Customer Feedback",
            "description": "Tell us what you think",
            "is_active": True,
            "sections": [
                {
                    "title": "Personal Information",
                    "description": "Basic details",
                    "order": 0,
                    "fields": [
                        {
                            "field_type": "text",
                            "label": "Full Name",
                            "is_required": True,
                            "order": 0
                        },
                        {
                            "field_type": "email",
                            "label": "Email",
                            "is_required": True,
                            "is_sensitive": True,
                            "order": 1
                        }
                    ]
                },
                {
                    "title": "Feedback",
                    "description": "Your thoughts",
                    "order": 1,
                    "fields": [
                        {
                            "field_type": "rating",
                            "label": "Overall Satisfaction",
                            "min_value": 1,
                            "max_value": 5,
                            "is_required": True,
                            "order": 0
                        },
                        {
                            "field_type": "textarea",
                            "label": "Comments",
                            "is_required": False,
                            "order": 1
                        }
                    ]
                }
            ]
        }
        
        serializer = SurveyCreateSerializer(data=data, context={"request": request})
        assert serializer.is_valid(), serializer.errors
        
        survey = serializer.save()
        
        assert survey.title == "Customer Feedback"
        assert survey.owner == user
        assert survey.sections.count() == 2
        
        section1 = survey.sections.get(order=0)
        assert section1.title == "Personal Information"
        assert section1.fields.count() == 2
        
        section2 = survey.sections.get(order=1)
        assert section2.title == "Feedback"
        assert section2.fields.count() == 2
        
        # Verify field details
        name_field = section1.fields.get(order=0)
        assert name_field.label == "Full Name"
        assert name_field.is_required is True
        
        email_field = section1.fields.get(order=1)
        assert email_field.is_sensitive is True
    
    def test_create_survey_without_sections(self):
        """Test creating a survey without sections."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        
        factory = APIRequestFactory()
        request = factory.post("/api/v1/surveys/")
        request.user = user
        
        data = {
            "title": "Empty Survey",
            "description": "No sections yet",
            "is_active": False
        }
        
        serializer = SurveyCreateSerializer(data=data, context={"request": request})
        assert serializer.is_valid()
        
        survey = serializer.save()
        
        assert survey.title == "Empty Survey"
        assert survey.sections.count() == 0


@pytest.mark.django_db
class TestSectionCreateSerializer:
    """Test SectionCreateSerializer."""
    
    def test_create_section_with_fields(self):
        """Test creating a section with nested fields."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        
        data = {
            "title": "Contact Information",
            "description": "How to reach you",
            "order": 0,
            "fields": [
                {
                    "field_type": "phone",
                    "label": "Phone Number",
                    "is_required": True,
                    "order": 0
                },
                {
                    "field_type": "email",
                    "label": "Email",
                    "is_required": True,
                    "order": 1
                }
            ]
        }
        
        serializer = SectionCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        
        section = serializer.save(survey=survey)
        
        assert section.title == "Contact Information"
        assert section.survey == survey
        assert section.fields.count() == 2
        
        phone_field = section.fields.get(order=0)
        assert phone_field.field_type == "phone"
        assert phone_field.label == "Phone Number"
