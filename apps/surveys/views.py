"""Views for Survey, Section, and Field API endpoints."""
from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import CanManageSurvey

from .cache import get_cached_survey, invalidate_survey_cache, set_cached_survey
from .models import Field, Section, Survey
from .serializers import (
    FieldSerializer,
    SectionCreateSerializer,
    SectionSerializer,
    SurveyCreateSerializer,
    SurveyDetailSerializer,
    SurveyListSerializer,
)


class SurveyViewSet(viewsets.ModelViewSet):
    """
    API endpoints for Survey management.
    
    Supports DRF URL versioning: /api/v1/surveys/, /api/v2/surveys/
    Implements FR 3.1 (select_related/prefetch_related) and FR 3.2 (caching).
    
    list: GET /api/{version}/surveys/
    create: POST /api/{version}/surveys/
    retrieve: GET /api/{version}/surveys/{id}/
    update: PUT/PATCH /api/{version}/surveys/{id}/
    destroy: DELETE /api/{version}/surveys/{id}/
    """
    
    permission_classes = [CanManageSurvey]
    
    def get_queryset(self):
        """Optimized queryset with prefetch for nested data."""
        return Survey.objects.select_related("owner").prefetch_related(
            Prefetch(
                "sections",
                queryset=Section.objects.prefetch_related("fields").order_by("order")
            )
        ).order_by("-created_at")
    
    def get_serializer_class(self):
        if self.action == "list":
            return SurveyListSerializer
        elif self.action == "create":
            return SurveyCreateSerializer
        return SurveyDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve survey with caching."""
        survey_id = kwargs.get("pk")
        
        # Try cache first
        cached_data = get_cached_survey(survey_id)
        if cached_data:
            return Response(cached_data)
        
        # Cache miss - fetch from DB
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Cache the result
        set_cached_survey(survey_id, serializer.data)
        
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Update survey and invalidate cache."""
        response = super().update(request, *args, **kwargs)
        invalidate_survey_cache(kwargs.get("pk"))
        return response
    
    def partial_update(self, request, *args, **kwargs):
        """Partial update survey and invalidate cache."""
        response = super().partial_update(request, *args, **kwargs)
        invalidate_survey_cache(kwargs.get("pk"))
        return response
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete survey and invalidate cache."""
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        invalidate_survey_cache(kwargs.get("pk"))
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None, **kwargs):
        """Create a copy of an existing survey."""
        survey = self.get_object()
        
        # Create new survey
        new_survey = Survey.objects.create(
            title=f"{survey.title} (Copy)",
            description=survey.description,
            owner=request.user,
            is_active=False,
        )
        
        # Copy sections and fields
        # TODO: refactor this to use bulk_create
        for section in survey.sections.all():
            new_section = Section.objects.create(
                survey=new_survey,
                title=section.title,
                description=section.description,
                order=section.order,
                logic_rules=section.logic_rules,
            )
            for field in section.fields.all():
                Field.objects.create(
                    section=new_section,
                    field_type=field.field_type,
                    label=field.label,
                    placeholder=field.placeholder,
                    help_text=field.help_text,
                    options=field.options,
                    is_required=field.is_required,
                    validation_regex=field.validation_regex,
                    validation_message=field.validation_message,
                    min_value=field.min_value,
                    max_value=field.max_value,
                    logic_rules=field.logic_rules,
                    dependency_config=field.dependency_config,
                    is_sensitive=field.is_sensitive,
                    order=field.order,
                )
        
        serializer = SurveyDetailSerializer(new_survey)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SectionViewSet(viewsets.ModelViewSet):
    """API endpoints for Section management within a survey."""
    
    permission_classes = [CanManageSurvey]
    
    def get_queryset(self):
        survey_pk = self.kwargs.get("survey_pk")
        return Section.objects.filter(survey_id=survey_pk).prefetch_related("fields").order_by("order")
    
    def get_serializer_class(self):
        if self.action == "create":
            return SectionCreateSerializer
        return SectionSerializer
    
    def perform_create(self, serializer):
        survey_pk = self.kwargs.get("survey_pk")
        survey = Survey.objects.get(pk=survey_pk)
        serializer.save(survey=survey)
        invalidate_survey_cache(survey_pk)
    
    def perform_update(self, serializer):
        serializer.save()
        invalidate_survey_cache(self.kwargs.get("survey_pk"))
    
    def perform_destroy(self, instance):
        survey_pk = self.kwargs.get("survey_pk")
        instance.delete()
        invalidate_survey_cache(survey_pk)


class FieldViewSet(viewsets.ModelViewSet):
    """API endpoints for Field management within a section."""
    
    permission_classes = [CanManageSurvey]
    serializer_class = FieldSerializer
    
    def get_queryset(self):
        section_pk = self.kwargs.get("section_pk")
        return Field.objects.filter(section_id=section_pk).order_by("order")
    
    def perform_create(self, serializer):
        section_pk = self.kwargs.get("section_pk")
        section = Section.objects.get(pk=section_pk)
        serializer.save(section=section)
        invalidate_survey_cache(section.survey_id)
    
    def perform_update(self, serializer):
        instance = serializer.save()
        invalidate_survey_cache(instance.section.survey_id)
    
    def perform_destroy(self, instance):
        survey_id = instance.section.survey_id
        instance.delete()
        invalidate_survey_cache(survey_id)


class PublicSurveyView(APIView):
    """
    Public endpoint for retrieving active surveys.
    No authentication required - for survey takers.
    
    GET /api/{version}/public/surveys/{id}/
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request, survey_id, version=None):
        """Retrieve active survey for public access."""
        # Try cache first
        cached_data = get_cached_survey(survey_id)
        if cached_data:
            # Verify survey is still active
            try:
                survey = Survey.objects.only('is_active').get(id=survey_id)
                if survey.is_active:
                    return Response(cached_data)
            except Survey.DoesNotExist:
                pass
        
        # Cache miss or inactive - fetch from DB
        try:
            survey = Survey.objects.select_related("owner").prefetch_related(
                Prefetch(
                    "sections",
                    queryset=Section.objects.prefetch_related("fields").order_by("order")
                )
            ).get(id=survey_id, is_active=True)
        except Survey.DoesNotExist:
            return Response(
                {"error": "Survey not found or inactive"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SurveyDetailSerializer(survey)
        
        # Cache the result
        set_cached_survey(survey_id, serializer.data)
        
        return Response(serializer.data)

