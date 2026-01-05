"""Views for Response and PartialResponse API endpoints."""
import uuid

from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response as DRFResponse
from rest_framework.views import APIView

from apps.audit.middleware import log_audit_event
from apps.audit.models import AuditAction
from apps.logic_engine import LogicEngine
from apps.surveys.models import Section, Survey
from apps.users.permissions import CanManageSurvey

from .models import PartialResponse, Response
from .serializers import (
    PartialResponseSerializer,
    ResponseSerializer,
    SubmissionSerializer,
)
from .tasks import export_responses_csv


class ResponseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for viewing survey responses.
    Admin/Analyst access only.
    
    list: GET /api/{version}/surveys/{survey_pk}/responses/
    retrieve: GET /api/{version}/surveys/{survey_pk}/responses/{id}/
    """
    
    permission_classes = [CanManageSurvey]
    serializer_class = ResponseSerializer
    
    def get_queryset(self):
        survey_pk = self.kwargs.get("survey_pk")
        return Response.objects.filter(
            survey_id=survey_pk
        ).select_related("survey", "user").order_by("-submitted_at")
    
    @action(detail=False, methods=["post"])
    def export(self, request, survey_pk=None, **kwargs):
        """Trigger async CSV export of responses."""
        export_responses_csv.delay(survey_pk, request.user.email)
        return DRFResponse(
            {"message": "Export started. You will receive an email when ready."},
            status=status.HTTP_202_ACCEPTED
        )


class PartialSaveView(APIView):
    """
    Endpoint for saving partial survey progress (heartbeat/auto-save).
    POST /api/{version}/surveys/{survey_id}/partial/
    
    Maps to FR 2.2: Partial Saves (Heartbeat).
    """
    
    permission_classes = [AllowAny]  # Allow anonymous submissions
    
    def post(self, request, survey_id, version=None):
        """Save or update partial response."""
        # Get or generate session token
        session_token = request.data.get("session_token")
        if not session_token:
            session_token = str(uuid.uuid4())
        
        # Get survey
        try:
            survey = Survey.objects.get(id=survey_id, is_active=True)
        except Survey.DoesNotExist:
            return DRFResponse(
                {"error": "Survey not found or inactive"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update or create partial response
        partial, created = PartialResponse.objects.update_or_create(
            survey=survey,
            session_token=session_token,
            defaults={
                "data": request.data.get("data", {}),
                "last_section_id": request.data.get("last_section_id"),
                "last_field_id": request.data.get("last_field_id"),
                "user": request.user if request.user.is_authenticated else None,
            }
        )
        
        serializer = PartialResponseSerializer(partial)
        return DRFResponse(
            {
                "session_token": session_token,
                "partial_response": serializer.data
            },
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED
        )
    
    def get(self, request, survey_id, version=None):
        """Retrieve existing partial response by session token."""
        session_token = request.query_params.get("session_token")
        
        if not session_token:
            return DRFResponse(
                {"error": "session_token query parameter required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            partial = PartialResponse.objects.get(
                survey_id=survey_id,
                session_token=session_token
            )
        except PartialResponse.DoesNotExist:
            return DRFResponse(
                {"error": "No saved progress found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = PartialResponseSerializer(partial)
        return DRFResponse(serializer.data)


class SubmitView(APIView):
    """
    Endpoint for final survey submission with validation.
    POST /api/{version}/surveys/{survey_id}/submit/
    
    Maps to FR 2.1: Real-time Validation.
    """
    
    permission_classes = [AllowAny]  # Allow anonymous submissions
    
    def post(self, request, survey_id, version=None):
        """Submit final survey response."""
        # Get survey with all sections and fields
        try:
            survey = Survey.objects.prefetch_related(
                Prefetch(
                    "sections",
                    queryset=Section.objects.prefetch_related("fields").order_by("order")
                )
            ).get(id=survey_id, is_active=True)
        except Survey.DoesNotExist:
            return DRFResponse(
                {"error": "Survey not found or inactive"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate submission
        serializer = SubmissionSerializer(
            data=request.data,
            context={"survey": survey, "request": request}
        )
        
        if not serializer.is_valid():
            return DRFResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Process sensitive fields - encrypt PII data
        submitted_data = serializer.validated_data["data"]
        encrypted_data = self._extract_sensitive_data(survey, submitted_data)
        
        # Create response
        response = Response.objects.create(
            survey=survey,
            user=request.user if request.user.is_authenticated else None,
            data=submitted_data,
            encrypted_data=encrypted_data,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
        
        # Clean up partial response if session token provided
        session_token = serializer.validated_data.get("session_token")
        if session_token:
            PartialResponse.objects.filter(
                survey=survey,
                session_token=session_token
            ).delete()
        
        # Audit log
        log_audit_event(
            action=AuditAction.CREATE,
            user=request.user if request.user.is_authenticated else None,
            obj=response,
            description=f"Survey response submitted for '{survey.title}'",
            request=request,
        )
        
        return DRFResponse(
            {"id": str(response.id), "message": "Survey submitted successfully"},
            status=status.HTTP_201_CREATED
        )
    
    def _extract_sensitive_data(self, survey, data):
        """Extract and return sensitive field values for encryption."""
        sensitive_values = {}
        
        for section in survey.sections.all():
            for field in section.fields.all():
                if field.is_sensitive:
                    field_id = str(field.id)
                    if field_id in data:
                        sensitive_values[field_id] = data[field_id]
        
        return str(sensitive_values) if sensitive_values else ""
    
    def _get_client_ip(self, request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
