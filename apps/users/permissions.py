"""
Custom permissions for ADSP using django-guardian.
"""
from rest_framework import permissions


class IsSurveyAdmin(permissions.BasePermission):
    """Check if user is in survey_admins group."""
    
    def has_permission(self, request, view):
        return request.user.groups.filter(name="survey_admins").exists()


class IsSurveyAnalyst(permissions.BasePermission):
    """Check if user is in survey_analysts group."""
    
    def has_permission(self, request, view):
        return request.user.groups.filter(name="survey_analysts").exists()


class IsSurveyViewer(permissions.BasePermission):
    """Check if user is in survey_viewers group."""
    
    def has_permission(self, request, view):
        return request.user.groups.filter(name="survey_viewers").exists()


class IsSurveyOwner(permissions.BasePermission):
    """Check if user is the owner of a survey."""
    
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class CanManageSurvey(permissions.BasePermission):
    """
    Custom permission for survey management.
    - Admins: Full access
    - Analysts: Read + limited write (no delete)
    - Viewers: Read only
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Admins can do anything
        if request.user.groups.filter(name="survey_admins").exists():
            return True
        
        # Analysts can read and create
        if request.user.groups.filter(name="survey_analysts").exists():
            return request.method in permissions.SAFE_METHODS + ("POST", "PATCH")
        
        # Viewers can only read
        if request.user.groups.filter(name="survey_viewers").exists():
            return request.method in permissions.SAFE_METHODS
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Owner has full access
        if hasattr(obj, "owner") and obj.owner == request.user:
            return True
        
        return self.has_permission(request, view)
