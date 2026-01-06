"""
Test Data Seeder

Creates realistic test data for development and testing purposes.

Usage:
    python manage.py shell < tests/seed_test_data.py
    
    # Or from Django shell:
    from tests.seed_test_data import seed_all_data
    seed_all_data()
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction

from apps.responses.models import PartialResponse, Response
from apps.surveys.models import Field, FieldType, Section, Survey
from apps.users.models import SURVEY_ADMIN_GROUP, SURVEY_ANALYST_GROUP, SURVEY_VIEWER_GROUP

User = get_user_model()


@transaction.atomic
def seed_users():
    """Create test users with different roles."""
    print("Creating users...")
    
    users = []
    
    # Admin users
    for i in range(1, 4):
        user, created = User.objects.get_or_create(
            username=f"admin{i}",
            defaults={
                'email': f"admin{i}@example.com",
                'is_active': True
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            # Add to admin group
            group, _ = Group.objects.get_or_create(name=SURVEY_ADMIN_GROUP)
            user.groups.add(group)
        users.append(user)
    
    # Analyst users
    for i in range(1, 3):
        user, created = User.objects.get_or_create(
            username=f"analyst{i}",
            defaults={
                'email': f"analyst{i}@example.com",
                'is_active': True
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            # Add to analyst group
            group, _ = Group.objects.get_or_create(name=SURVEY_ANALYST_GROUP)
            user.groups.add(group)
        users.append(user)
    
    # Viewer users
    for i in range(1, 3):
        user, created = User.objects.get_or_create(
            username=f"viewer{i}",
            defaults={
                'email': f"viewer{i}@example.com",
                'is_active': True
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            # Add to viewer group
            group, _ = Group.objects.get_or_create(name=SURVEY_VIEWER_GROUP)
            user.groups.add(group)
        users.append(user)
    
    print(f"Created {len(users)} users")
    return users


@transaction.atomic
def seed_surveys(users):
    """Create test surveys."""
    print("Creating surveys...")
    
    # Filter admin users by checking their groups
    admin_users = [u for u in users if u.groups.filter(name=SURVEY_ADMIN_GROUP).exists()]
    surveys = []
    
    # Customer Satisfaction Survey
    survey1 = Survey.objects.create(
        title="Customer Satisfaction Survey",
        description="Help us improve our services",
        owner=admin_users[0],
        is_active=True
    )
    
    section1 = Section.objects.create(
        survey=survey1,
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
    
    section2 = Section.objects.create(
        survey=survey1,
        title="Feedback",
        description="Your experience",
        order=1
    )
    
    Field.objects.create(
        section=section2,
        field_type=FieldType.RATING,
        label="Overall Satisfaction",
        help_text="Rate from 1 (poor) to 5 (excellent)",
        min_value=1,
        max_value=5,
        is_required=True,
        order=0
    )
    
    Field.objects.create(
        section=section2,
        field_type=FieldType.TEXTAREA,
        label="Comments",
        placeholder="Tell us more about your experience...",
        is_required=False,
        order=1
    )
    
    surveys.append(survey1)
    
    # Employee Onboarding Survey
    survey2 = Survey.objects.create(
        title="Employee Onboarding Survey",
        description="New employee information",
        owner=admin_users[0],
        is_active=True
    )
    
    section1 = Section.objects.create(
        survey=survey2,
        title="Personal Details",
        order=0
    )
    
    Field.objects.create(
        section=section1,
        field_type=FieldType.TEXT,
        label="First Name",
        is_required=True,
        order=0
    )
    
    Field.objects.create(
        section=section1,
        field_type=FieldType.TEXT,
        label="Last Name",
        is_required=True,
        order=1
    )
    
    Field.objects.create(
        section=section1,
        field_type=FieldType.DATE,
        label="Date of Birth",
        is_required=True,
        is_sensitive=True,
        order=2
    )
    
    Field.objects.create(
        section=section1,
        field_type=FieldType.PHONE,
        label="Phone Number",
        is_required=True,
        is_sensitive=True,
        order=3
    )
    
    section2 = Section.objects.create(
        survey=survey2,
        title="Employment Information",
        order=1
    )
    
    Field.objects.create(
        section=section2,
        field_type=FieldType.SELECT,
        label="Department",
        options=[
            {"value": "eng", "label": "Engineering"},
            {"value": "sales", "label": "Sales"},
            {"value": "hr", "label": "Human Resources"},
            {"value": "finance", "label": "Finance"}
        ],
        is_required=True,
        order=0
    )
    
    Field.objects.create(
        section=section2,
        field_type=FieldType.SELECT,
        label="Position Level",
        options=[
            {"value": "junior", "label": "Junior"},
            {"value": "mid", "label": "Mid-Level"},
            {"value": "senior", "label": "Senior"},
            {"value": "lead", "label": "Lead"}
        ],
        is_required=True,
        order=1
    )
    
    surveys.append(survey2)
    
    # Event Registration Survey
    survey3 = Survey.objects.create(
        title="Event Registration",
        description="Register for our upcoming conference",
        owner=admin_users[1] if len(admin_users) > 1 else admin_users[0],
        is_active=True
    )
    
    section1 = Section.objects.create(
        survey=survey3,
        title="Attendee Information",
        order=0
    )
    
    Field.objects.create(
        section=section1,
        field_type=FieldType.TEXT,
        label="Full Name",
        is_required=True,
        order=0
    )
    
    Field.objects.create(
        section=section1,
        field_type=FieldType.EMAIL,
        label="Email",
        is_required=True,
        is_sensitive=True,
        order=1
    )
    
    Field.objects.create(
        section=section1,
        field_type=FieldType.TEXT,
        label="Company",
        is_required=False,
        order=2
    )
    
    section2 = Section.objects.create(
        survey=survey3,
        title="Session Preferences",
        order=1
    )
    
    Field.objects.create(
        section=section2,
        field_type=FieldType.MULTISELECT,
        label="Sessions of Interest",
        options=[
            {"value": "ai", "label": "AI & Machine Learning"},
            {"value": "cloud", "label": "Cloud Architecture"},
            {"value": "security", "label": "Cybersecurity"},
            {"value": "devops", "label": "DevOps Best Practices"}
        ],
        is_required=True,
        order=0
    )
    
    Field.objects.create(
        section=section2,
        field_type=FieldType.CHECKBOX,
        label="Dietary Restrictions",
        options=[
            {"value": "vegetarian", "label": "Vegetarian"},
            {"value": "vegan", "label": "Vegan"},
            {"value": "gluten_free", "label": "Gluten-Free"},
            {"value": "none", "label": "None"}
        ],
        is_required=False,
        order=1
    )
    
    surveys.append(survey3)
    
    print(f"Created {len(surveys)} surveys")
    return surveys


@transaction.atomic
def seed_responses(surveys):
    """Create test responses."""
    print("Creating responses...")
    
    responses_created = 0
    
    for survey in surveys:
        # Create 5-10 responses per survey
        for i in range(5):
            response_data = {}
            
            for section in survey.sections.all():
                for field in section.fields.all():
                    field_id = str(field.id)
                    
                    # Generate sample data based on field type
                    if field.field_type == FieldType.TEXT:
                        response_data[field_id] = f"Sample text {i}"
                    elif field.field_type == FieldType.EMAIL:
                        response_data[field_id] = f"user{i}@example.com"
                    elif field.field_type == FieldType.PHONE:
                        response_data[field_id] = f"+1-555-{1000 + i}"
                    elif field.field_type == FieldType.NUMBER:
                        response_data[field_id] = i + 1
                    elif field.field_type == FieldType.RATING:
                        response_data[field_id] = (i % 5) + 1
                    elif field.field_type == FieldType.SELECT:
                        if field.options:
                            response_data[field_id] = field.options[i % len(field.options)]["value"]
                    elif field.field_type == FieldType.MULTISELECT:
                        if field.options:
                            response_data[field_id] = [opt["value"] for opt in field.options[:2]]
                    elif field.field_type == FieldType.CHECKBOX:
                        if field.options:
                            response_data[field_id] = [field.options[0]["value"]]
                    elif field.field_type == FieldType.TEXTAREA:
                        response_data[field_id] = f"This is a longer text response for iteration {i}. It contains multiple sentences."
                    elif field.field_type == FieldType.DATE:
                        response_data[field_id] = "1990-01-01"
            
            Response.objects.create(
                survey=survey,
                data=response_data,
                ip_address=f"192.168.1.{i + 1}",
                user_agent="Mozilla/5.0 (Test Data)",
                completion_time_seconds=120 + (i * 10)
            )
            responses_created += 1
    
    print(f"Created {responses_created} responses")


@transaction.atomic
def seed_partial_responses(surveys):
    """Create test partial responses."""
    print("Creating partial responses...")
    
    partials_created = 0
    
    for survey in surveys[:2]:  # Only for first 2 surveys
        for i in range(3):
            partial_data = {}
            
            # Fill only first section
            first_section = survey.sections.first()
            if first_section:
                for field in first_section.fields.all():
                    field_id = str(field.id)
                    if field.field_type == FieldType.TEXT:
                        partial_data[field_id] = f"Partial {i}"
                    elif field.field_type == FieldType.EMAIL:
                        partial_data[field_id] = f"partial{i}@example.com"
            
            PartialResponse.objects.create(
                survey=survey,
                session_token=f"test-session-{survey.id}-{i}",
                data=partial_data,
                last_section_id=first_section.id if first_section else None
            )
            partials_created += 1
    
    print(f"Created {partials_created} partial responses")


def seed_all_data():
    """Seed all test data."""
    print("=" * 80)
    print("Seeding Test Data")
    print("=" * 80)
    
    users = seed_users()
    surveys = seed_surveys(users)
    seed_responses(surveys)
    seed_partial_responses(surveys)
    
    print("=" * 80)
    print("Test data seeding complete!")
    print("=" * 80)
    print("\nTest Accounts:")
    print("  Admin:   admin1@example.com / testpass123")
    print("  Analyst: analyst1@example.com / testpass123")
    print("  Viewer:  viewer1@example.com / testpass123")
    print()


if __name__ == '__main__':
    seed_all_data()
