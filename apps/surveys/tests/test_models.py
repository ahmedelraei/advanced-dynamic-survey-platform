"""Unit tests for Survey, Section, and Field models."""
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from conftest import create_user_with_group
from apps.users.models import SURVEY_ADMIN_GROUP, SURVEY_ANALYST_GROUP, SURVEY_VIEWER_GROUP

from apps.surveys.models import Field, FieldType, Section, Survey

User = get_user_model()


@pytest.mark.django_db
class TestSurveyModel:
    """Test Survey model functionality."""
    
    def test_create_survey(self):
        """Test creating a basic survey."""
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
        
        assert survey.id is not None
        assert survey.title == "Test Survey"
        assert survey.version == 1
        assert survey.owner == user
        assert str(survey) == "Test Survey (v1)"
    
    def test_survey_requires_owner(self):
        """Test that survey requires an owner."""
        with pytest.raises(IntegrityError):
            Survey.objects.create(
                title="Test Survey",
                description="Test Description"
            )
    
    def test_survey_default_values(self):
        """Test survey default values."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        
        survey = Survey.objects.create(
            title="Test Survey",
            owner=user
        )
        
        assert survey.is_active is True
        assert survey.version == 1
        assert survey.description == ""
    
    def test_survey_ordering(self):
        """Test surveys are ordered by created_at descending."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        
        survey1 = Survey.objects.create(title="First", owner=user)
        survey2 = Survey.objects.create(title="Second", owner=user)
        survey3 = Survey.objects.create(title="Third", owner=user)
        
        surveys = list(Survey.objects.all())
        assert surveys[0] == survey3
        assert surveys[1] == survey2
        assert surveys[2] == survey1


@pytest.mark.django_db
class TestSectionModel:
    """Test Section model functionality."""
    
    def test_create_section(self):
        """Test creating a section."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        
        section = Section.objects.create(
            survey=survey,
            title="Personal Information",
            description="Basic details",
            order=0
        )
        
        assert section.id is not None
        assert section.survey == survey
        assert section.title == "Personal Information"
        assert section.order == 0
        assert str(section) == "Test Survey - Personal Information"
    
    def test_section_logic_rules_default(self):
        """Test section logic_rules defaults to empty dict."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        section = Section.objects.create(survey=survey, title="Test Section")
        
        assert section.logic_rules == {}
    
    def test_section_logic_rules_storage(self):
        """Test storing complex logic rules in JSONB."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        
        logic_rules = {
            "conditions": [
                {"field_id": "field-uuid", "operator": "equals", "value": "USA"}
            ],
            "logic": "and",
            "action": "show"
        }
        
        section = Section.objects.create(
            survey=survey,
            title="Test Section",
            logic_rules=logic_rules
        )
        
        # Refresh from DB
        section.refresh_from_db()
        assert section.logic_rules == logic_rules
    
    def test_section_cascade_delete(self):
        """Test sections are deleted when survey is deleted."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        section = Section.objects.create(survey=survey, title="Test Section")
        
        survey.delete()
        
        assert not Section.objects.filter(id=section.id).exists()


@pytest.mark.django_db
class TestFieldModel:
    """Test Field model functionality."""
    
    def test_create_field(self):
        """Test creating a field."""
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
        
        assert field.id is not None
        assert field.section == section
        assert field.field_type == FieldType.TEXT
        assert field.label == "Full Name"
        assert field.is_required is True
        assert str(field) == "Test Section - Full Name"
    
    def test_field_types(self):
        """Test all field types are valid."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        section = Section.objects.create(survey=survey, title="Test Section")
        
        for field_type in FieldType.choices:
            field = Field.objects.create(
                section=section,
                field_type=field_type[0],
                label=f"Test {field_type[1]}",
                order=0
            )
            assert field.field_type == field_type[0]
    
    def test_field_options_storage(self):
        """Test storing field options in JSONB."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        section = Section.objects.create(survey=survey, title="Test Section")
        
        options = [
            {"value": "usa", "label": "United States"},
            {"value": "uk", "label": "United Kingdom"},
            {"value": "ca", "label": "Canada"}
        ]
        
        field = Field.objects.create(
            section=section,
            field_type=FieldType.SELECT,
            label="Country",
            options=options
        )
        
        field.refresh_from_db()
        assert field.options == options
    
    def test_field_validation_rules(self):
        """Test field validation configuration."""
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
            field_type=FieldType.NUMBER,
            label="Age",
            is_required=True,
            min_value=18,
            max_value=100,
            validation_message="Age must be between 18 and 100"
        )
        
        assert field.min_value == 18
        assert field.max_value == 100
        assert field.validation_message == "Age must be between 18 and 100"
    
    def test_field_dependency_config(self):
        """Test cross-section dependency configuration."""
        user = create_user_with_group(
            username="test",
            email="test@example.com",
            password="testpass123",
            group_name=SURVEY_ADMIN_GROUP
        )
        survey = Survey.objects.create(title="Test Survey", owner=user)
        section = Section.objects.create(survey=survey, title="Test Section")
        
        dependency_config = {
            "depends_on": "country-field-uuid",
            "filter_by": "country"
        }
        
        field = Field.objects.create(
            section=section,
            field_type=FieldType.SELECT,
            label="State",
            dependency_config=dependency_config
        )
        
        field.refresh_from_db()
        assert field.dependency_config == dependency_config
    
    def test_field_sensitive_flag(self):
        """Test marking fields as sensitive (PII)."""
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
            field_type=FieldType.EMAIL,
            label="Email Address",
            is_sensitive=True
        )
        
        assert field.is_sensitive is True
    
    def test_field_cascade_delete(self):
        """Test fields are deleted when section is deleted."""
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
            label="Test Field"
        )
        
        section.delete()
        
        assert not Field.objects.filter(id=field.id).exists()
