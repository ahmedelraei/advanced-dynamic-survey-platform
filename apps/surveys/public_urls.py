"""URL routes for public survey access (no authentication)."""
from django.urls import path

from .views import PublicSurveyView

urlpatterns = [
    path("surveys/<uuid:survey_id>/", PublicSurveyView.as_view(), name="public-survey-detail"),
]
