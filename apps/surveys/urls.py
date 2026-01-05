"""URL routes for Survey API endpoints."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views import FieldViewSet, SectionViewSet, SurveyViewSet

# Main router for surveys
router = DefaultRouter()
router.register(r"surveys", SurveyViewSet, basename="survey")

# Nested router for sections within surveys
surveys_router = routers.NestedDefaultRouter(router, r"surveys", lookup="survey")
surveys_router.register(r"sections", SectionViewSet, basename="survey-sections")

# Nested router for fields within sections
sections_router = routers.NestedDefaultRouter(surveys_router, r"sections", lookup="section")
sections_router.register(r"fields", FieldViewSet, basename="section-fields")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(surveys_router.urls)),
    path("", include(sections_router.urls)),
]
