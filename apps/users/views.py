"""Authentication views for client users."""
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Organization
from .permissions import IsSurveyAdmin
from .serializers import (
    LoginSerializer,
    OrganizationSerializer,
    UserManagementSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)

User = get_user_model()


class CSRFTokenView(APIView):
    """
    Get CSRF token for API clients.
    GET /api/{version}/auth/csrf/
    """
    
    permission_classes = [AllowAny]
    
    @method_decorator(ensure_csrf_cookie)
    def get(self, request, version=None):
        """Return CSRF token in response and set cookie."""
        csrf_token = get_token(request)
        return Response({
            "csrfToken": csrf_token,
            "message": "CSRF token generated. Check cookies for 'csrftoken'."
        })


class RegisterView(APIView):
    """
    Register a new client account.
    POST /api/{version}/auth/register/
    
    Note: Users registered this way have no organization or permissions.
    They must be assigned to an organization by an admin.
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request, version=None):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Auto-login after registration
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return Response(
                {
                    "message": "Registration successful. Contact your admin to be assigned to an organization.",
                    "user": UserSerializer(user).data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    Login for client users.
    POST /api/{version}/auth/login/
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request, version=None):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data["username"]
            password = serializer.validated_data["password"]
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return Response({
                    "message": "Login successful",
                    "user": UserSerializer(user).data
                })
            else:
                return Response(
                    {"error": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    Logout current user.
    POST /api/{version}/auth/logout/
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, version=None):
        logout(request)
        return Response({"message": "Logout successful"})


class ProfileView(APIView):
    """
    Get current user profile.
    GET /api/{version}/auth/profile/
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, version=None):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request, version=None):
        """Update user profile."""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    API endpoints for Organization management (Admin only).
    
    list: GET /api/{version}/organizations/
    create: POST /api/{version}/organizations/
    retrieve: GET /api/{version}/organizations/{id}/
    update: PUT/PATCH /api/{version}/organizations/{id}/
    destroy: DELETE /api/{version}/organizations/{id}/
    """
    
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsSurveyAdmin]
    
    @action(detail=True, methods=["get"])
    def users(self, request, pk=None, **kwargs):
        """Get all users in this organization."""
        organization = self.get_object()
        users = organization.users.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    API endpoints for User management within organizations (Admin only).
    
    Admins can create users and assign them to organizations with specific roles.
    
    list: GET /api/{version}/users/
    create: POST /api/{version}/users/
    retrieve: GET /api/{version}/users/{id}/
    update: PUT/PATCH /api/{version}/users/{id}/
    destroy: DELETE /api/{version}/users/{id}/
    """
    
    serializer_class = UserManagementSerializer
    permission_classes = [IsAuthenticated, IsSurveyAdmin]
    
    def get_queryset(self):
        """Admins can see all users, or filter by organization."""
        queryset = User.objects.select_related("organization").prefetch_related("groups")
        
        # Filter by organization if provided
        org_id = self.request.query_params.get("organization")
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        
        return queryset.order_by("-date_joined")
    
    @action(detail=True, methods=["post"])
    def assign_role(self, request, pk=None, **kwargs):
        """Assign a role to a user."""
        user = self.get_object()
        role = request.data.get("role")
        
        if not role:
            return Response(
                {"error": "Role is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.contrib.auth.models import Group
        from .models import SURVEY_ADMIN_GROUP, SURVEY_ANALYST_GROUP, SURVEY_VIEWER_GROUP
        
        valid_roles = [SURVEY_ADMIN_GROUP, SURVEY_ANALYST_GROUP, SURVEY_VIEWER_GROUP]
        if role not in valid_roles:
            return Response(
                {"error": f"Invalid role. Must be one of: {', '.join(valid_roles)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Clear existing groups and assign new role
        user.groups.clear()
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)
        
        return Response({
            "message": f"User assigned to role: {role}",
            "user": UserSerializer(user).data
        })
    
    @action(detail=True, methods=["post"])
    def assign_organization(self, request, pk=None, **kwargs):
        """Assign a user to an organization."""
        user = self.get_object()
        org_id = request.data.get("organization_id")
        
        if not org_id:
            return Response(
                {"error": "organization_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            organization = Organization.objects.get(id=org_id)
            user.organization = organization
            user.save()
            
            return Response({
                "message": f"User assigned to organization: {organization.name}",
                "user": UserSerializer(user).data
            })
        except Organization.DoesNotExist:
            return Response(
                {"error": "Organization not found"},
                status=status.HTTP_404_NOT_FOUND
            )
