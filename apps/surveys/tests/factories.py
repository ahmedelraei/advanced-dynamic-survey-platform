"""Factory Boy factories for creating test data."""
import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from factory.django import DjangoModelFactory

from apps.responses.models import PartialResponse, Response
from apps.surveys.models import Field, FieldType, Section, Survey
from apps.users.models import SURVEY_ADMIN_GROUP, SURVEY_ANALYST_GROUP, SURVEY_VIEWER_GROUP

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    is_active = True
    
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        """Add user to viewer group by default."""
        if not create:
            return
        
        if extracted:
            for group in extracted:
                self.groups.add(group)
        else:
            # Default to viewer group
            group, _ = Group.objects.get_or_create(name=SURVEY_VIEWER_GROUP)
            self.groups.add(group)


class AdminUserFactory(UserFactory):
    """Factory for creating Admin users."""
    
    username = factory.Sequence(lambda n: f"admin{n}")
    email = factory.Sequence(lambda n: f"admin{n}@example.com")
    
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        """Add user to admin group."""
        if not create:
            return
        
        group, _ = Group.objects.get_or_create(name=SURVEY_ADMIN_GROUP)
        self.groups.add(group)


class AnalystUserFactory(UserFactory):
    """Factory for creating Analyst users."""
    
    username = factory.Sequence(lambda n: f"analyst{n}")
    email = factory.Sequence(lambda n: f"analyst{n}@example.com")
    
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        """Add user to analyst group."""
        if not create:
            return
        
        group, _ = Group.objects.get_or_create(name=SURVEY_ANALYST_GROUP)
        self.groups.add(group)


class SurveyFactory(DjangoModelFactory):
    """Factory for creating Survey instances."""
    
    class Meta:
        model = Survey
    
    title = factory.Sequence(lambda n: f"Survey {n}")
    description = factory.Faker("text", max_nb_chars=200)
    owner = factory.SubFactory(AdminUserFactory)
    is_active = True
    version = 1


class SectionFactory(DjangoModelFactory):
    """Factory for creating Section instances."""
    
    class Meta:
        model = Section
    
    survey = factory.SubFactory(SurveyFactory)
    title = factory.Sequence(lambda n: f"Section {n}")
    description = factory.Faker("text", max_nb_chars=100)
    order = factory.Sequence(lambda n: n)
    logic_rules = {}


class FieldFactory(DjangoModelFactory):
    """Factory for creating Field instances."""
    
    class Meta:
        model = Field
    
    section = factory.SubFactory(SectionFactory)
    field_type = FieldType.TEXT
    label = factory.Sequence(lambda n: f"Field {n}")
    placeholder = factory.Faker("sentence", nb_words=3)
    help_text = ""
    options = []
    is_required = False
    validation_regex = ""
    validation_message = ""
    min_value = None
    max_value = None
    logic_rules = {}
    dependency_config = {}
    is_sensitive = False
    order = factory.Sequence(lambda n: n)


class TextFieldFactory(FieldFactory):
    """Factory for text fields."""
    
    field_type = FieldType.TEXT


class EmailFieldFactory(FieldFactory):
    """Factory for email fields."""
    
    field_type = FieldType.EMAIL
    is_sensitive = True


class SelectFieldFactory(FieldFactory):
    """Factory for select fields."""
    
    field_type = FieldType.SELECT
    options = [
        {"value": "option1", "label": "Option 1"},
        {"value": "option2", "label": "Option 2"},
        {"value": "option3", "label": "Option 3"}
    ]


class NumberFieldFactory(FieldFactory):
    """Factory for number fields."""
    
    field_type = FieldType.NUMBER
    min_value = 0
    max_value = 100


class ResponseFactory(DjangoModelFactory):
    """Factory for creating Response instances."""
    
    class Meta:
        model = Response
    
    survey = factory.SubFactory(SurveyFactory)
    user = factory.SubFactory(UserFactory)
    data = {}
    encrypted_data = ""
    ip_address = factory.Faker("ipv4")
    user_agent = factory.Faker("user_agent")
    completion_time_seconds = factory.Faker("random_int", min=30, max=600)


class AnonymousResponseFactory(ResponseFactory):
    """Factory for anonymous responses."""
    
    user = None


class PartialResponseFactory(DjangoModelFactory):
    """Factory for creating PartialResponse instances."""
    
    class Meta:
        model = PartialResponse
    
    survey = factory.SubFactory(SurveyFactory)
    session_token = factory.Faker("uuid4")
    user = None
    data = {}
    last_section_id = None
    last_field_id = None


class CompleteSurveyFactory(SurveyFactory):
    """Factory for creating a complete survey with sections and fields."""
    
    @factory.post_generation
    def sections(self, create, extracted, **kwargs):
        """Create sections with fields after survey creation."""
        if not create:
            return
        
        # Create 3 sections by default
        num_sections = extracted if extracted else 3
        
        for i in range(num_sections):
            section = SectionFactory(survey=self, order=i)
            
            # Create 3-5 fields per section
            num_fields = 3 if i == 0 else 4 if i == 1 else 5
            
            for j in range(num_fields):
                if j == 0:
                    TextFieldFactory(section=section, order=j, is_required=True)
                elif j == 1:
                    EmailFieldFactory(section=section, order=j, is_required=False)
                elif j == 2:
                    SelectFieldFactory(section=section, order=j, is_required=True)
                elif j == 3:
                    NumberFieldFactory(section=section, order=j, is_required=False)
                else:
                    FieldFactory(
                        section=section,
                        field_type=FieldType.TEXTAREA,
                        order=j,
                        is_required=False
                    )
