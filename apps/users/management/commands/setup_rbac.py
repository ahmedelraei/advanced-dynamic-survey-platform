"""Management command to create RBAC groups and permissions."""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from apps.surveys.models import Survey, Section, Field
from apps.responses.models import Response, PartialResponse


class Command(BaseCommand):
    help = 'Create RBAC groups with appropriate permissions'

    def handle(self, *args, **options):
        # Create groups
        admin_group, _ = Group.objects.get_or_create(name='survey_admins')
        analyst_group, _ = Group.objects.get_or_create(name='survey_analysts')
        viewer_group, _ = Group.objects.get_or_create(name='survey_viewers')

        # Get content types
        survey_ct = ContentType.objects.get_for_model(Survey)
        section_ct = ContentType.objects.get_for_model(Section)
        field_ct = ContentType.objects.get_for_model(Field)
        response_ct = ContentType.objects.get_for_model(Response)
        partial_ct = ContentType.objects.get_for_model(PartialResponse)

        # Admin permissions (full access)
        admin_permissions = Permission.objects.filter(
            content_type__in=[survey_ct, section_ct, field_ct, response_ct, partial_ct]
        )
        admin_group.permissions.set(admin_permissions)

        # Analyst permissions (read + create + update, no delete)
        analyst_permissions = Permission.objects.filter(
            content_type__in=[survey_ct, section_ct, field_ct, response_ct, partial_ct],
            codename__in=[
                'view_survey', 'add_survey', 'change_survey',
                'view_section', 'add_section', 'change_section',
                'view_field', 'add_field', 'change_field',
                'view_response', 'view_partialresponse',
            ]
        )
        analyst_group.permissions.set(analyst_permissions)

        # Viewer permissions (read only)
        viewer_permissions = Permission.objects.filter(
            content_type__in=[survey_ct, section_ct, field_ct, response_ct, partial_ct],
            codename__startswith='view_'
        )
        viewer_group.permissions.set(viewer_permissions)

        self.stdout.write(self.style.SUCCESS('Successfully created RBAC groups:'))
        self.stdout.write(f'  - survey_admins: {admin_permissions.count()} permissions')
        self.stdout.write(f'  - survey_analysts: {analyst_permissions.count()} permissions')
        self.stdout.write(f'  - survey_viewers: {viewer_permissions.count()} permissions')
