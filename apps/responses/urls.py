"""URL routes for Response API endpoints."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from apps.surveys.urls import router as surveys_router

from .views import PartialSaveView, ResponseViewSet, SubmitView

# Nested router for responses within surveys
responses_router = routers.NestedDefaultRouter(surveys_router, r"surveys", lookup="survey")
responses_router.register(r"responses", ResponseViewSet, basename="survey-responses")

urlpatterns = [
    path("", include(responses_router.urls)),
    # Direct submission endpoints
    path("surveys/<uuid:survey_id>/partial/", PartialSaveView.as_view(), name="partial-save"),
    path("surveys/<uuid:survey_id>/submit/", SubmitView.as_view(), name="submit"),
]
