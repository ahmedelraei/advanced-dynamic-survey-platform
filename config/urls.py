"""
ADSP URL Configuration with DRF versioning.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.responses.views import PartialSaveView, SubmitView

# API URL patterns - versioned (authenticated - for clients/admins)
api_v1_patterns = [
    path("auth/", include("apps.users.urls")),
    path("", include("apps.surveys.urls")),
    path("", include("apps.responses.urls")),
]

# Public API patterns (no authentication - for survey takers)
public_api_patterns = [
    path("", include("apps.surveys.public_urls")),
    # Public endpoints for survey takers
    path("surveys/<uuid:survey_id>/partial/", PartialSaveView.as_view(), name="public-partial-save"),
    path("surveys/<uuid:survey_id>/submit/", SubmitView.as_view(), name="public-submit"),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # API v1 - authenticated (for clients managing surveys)
    path("api/<str:version>/", include((api_v1_patterns, "api"), namespace="api")),
    
    # Public API - unauthenticated (for survey takers)
    path("api/<str:version>/public/", include((public_api_patterns, "public_api"))),
    
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

# Debug toolbar (development only)
if settings.DEBUG:
    urlpatterns = [
        path("__debug__/", include("debug_toolbar.urls")),
    ] + urlpatterns
