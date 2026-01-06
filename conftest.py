"""
Shared pytest fixtures and configuration for all tests.

This module provides common fixtures used across all test modules.
"""
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from apps.surveys.models import Field, FieldType, Section, Survey
from apps.users.models import SURVEY_ADMIN_GROUP, SURVEY_ANALYST_GROUP, SURVEY_VIEWER_GROUP

User = get_user_model()


def create_user_with_group(username, email, password, group_name):
    """Helper function to create a user with a specific group."""
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        is_active=True
    )
    if group_name:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
    return user


@pytest.fixture
def api_client():
    """Create a DRF API client for testing."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    return create_user_with_group(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
        group_name=SURVEY_ADMIN_GROUP
    )


@pytest.fixture
def analyst_user(db):
    """Create an analyst user."""
    return create_user_with_group(
        username="analyst",
        email="analyst@example.com",
        password="analystpass123",
        group_name=SURVEY_ANALYST_GROUP
    )


@pytest.fixture
def viewer_user(db):
    """Create a viewer user."""
    return create_user_with_group(
        username="viewer",
        email="viewer@example.com",
        password="viewerpass123",
        group_name=SURVEY_VIEWER_GROUP
    )


@pytest.fixture
def authenticated_client(api_client, admin_user):
    """Create an authenticated API client with admin user."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def sample_survey(db, admin_user):
    """Create a sample survey for testing."""
    return Survey.objects.create(
        title="Sample Survey",
        description="A sample survey for testing",
        owner=admin_user,
        is_active=True
    )


@pytest.fixture
def complete_survey(db, admin_user):
    """Create a complete survey with sections and fields."""
    survey = Survey.objects.create(
        title="Complete Survey",
        description="A complete survey with sections and fields",
        owner=admin_user,
        is_active=True
    )
    
    # Section 1: Personal Information
    section1 = Section.objects.create(
        survey=survey,
        title="Personal Information",
        description="Basic details",
        order=0
    )
    
    Field.objects.create(
        section=section1,
        field_type=FieldType.TEXT,
        label="Full Name",
        placeholder="Enter your full name",
        is_required=True,
        order=0
    )
    
    Field.objects.create(
        section=section1,
        field_type=FieldType.EMAIL,
        label="Email Address",
        placeholder="you@example.com",
        is_required=True,
        is_sensitive=True,
        order=1
    )
    
    Field.objects.create(
        section=section1,
        field_type=FieldType.PHONE,
        label="Phone Number",
        is_required=False,
        is_sensitive=True,
        order=2
    )
    
    # Section 2: Preferences
    section2 = Section.objects.create(
        survey=survey,
        title="Preferences",
        description="Your preferences",
        order=1
    )
    
    Field.objects.create(
        section=section2,
        field_type=FieldType.SELECT,
        label="Country",
        options=[
            {"value": "usa", "label": "United States"},
            {"value": "uk", "label": "United Kingdom"},
            {"value": "ca", "label": "Canada"}
        ],
        is_required=True,
        order=0
    )
    
    Field.objects.create(
        section=section2,
        field_type=FieldType.RATING,
        label="Satisfaction",
        min_value=1,
        max_value=5,
        is_required=True,
        order=1
    )
    
    Field.objects.create(
        section=section2,
        field_type=FieldType.TEXTAREA,
        label="Comments",
        placeholder="Any additional comments...",
        is_required=False,
        order=2
    )
    
    return survey


@pytest.fixture
def survey_with_logic(db, admin_user):
    """Create a survey with conditional logic rules."""
    survey = Survey.objects.create(
        title="Survey with Logic",
        description="Survey with conditional logic",
        owner=admin_user,
        is_active=True
    )
    
    section1 = Section.objects.create(
        survey=survey,
        title="Basic Info",
        order=0
    )
    
    country_field = Field.objects.create(
        section=section1,
        field_type=FieldType.SELECT,
        label="Country",
        options=[
            {"value": "usa", "label": "United States"},
            {"value": "other", "label": "Other"}
        ],
        is_required=True,
        order=0
    )
    
    # Section 2 only shows if country is USA
    section2 = Section.objects.create(
        survey=survey,
        title="US-Specific Questions",
        order=1,
        logic_rules={
            "conditions": [
                {
                    "field_id": str(country_field.id),
                    "operator": "equals",
                    "value": "usa"
                }
            ],
            "logic": "and",
            "action": "show"
        }
    )
    
    Field.objects.create(
        section=section2,
        field_type=FieldType.SELECT,
        label="State",
        options=[
            {"value": "ca", "label": "California"},
            {"value": "ny", "label": "New York"},
            {"value": "tx", "label": "Texas"}
        ],
        is_required=True,
        order=0
    )
    
    return survey


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Automatically enable database access for all tests.
    This is a convenience fixture to avoid marking every test with @pytest.mark.django_db.
    """
    pass


@pytest.fixture
def mock_redis(mocker):
    """Mock Redis for testing without actual Redis connection."""
    mock_cache = mocker.patch('django.core.cache.cache')
    mock_cache.get.return_value = None
    mock_cache.set.return_value = True
    mock_cache.delete.return_value = True
    return mock_cache


@pytest.fixture
def mock_celery(mocker):
    """Mock Celery tasks for testing without actual task queue."""
    return mocker.patch('celery.app.task.Task.apply_async')


# Pytest configuration hooks
def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "load: mark test as a load test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-mark tests based on file location
        if "test_models.py" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "test_api.py" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "test_security.py" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        elif "locustfile.py" in str(item.fspath):
            item.add_marker(pytest.mark.load)
