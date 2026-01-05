"""URL routes for authentication endpoints."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CSRFTokenView,
    LoginView,
    LogoutView,
    OrganizationViewSet,
    ProfileView,
    RegisterView,
    UserManagementViewSet,
)

# Router for viewsets
router = DefaultRouter()
router.register(r"organizations", OrganizationViewSet, basename="organization")
router.register(r"users", UserManagementViewSet, basename="user-management")

urlpatterns = [
    # Authentication endpoints
    path("csrf/", CSRFTokenView.as_view(), name="csrf_token"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    
    # Organization and User Management (Admin only)
    path("", include(router.urls)),
]
