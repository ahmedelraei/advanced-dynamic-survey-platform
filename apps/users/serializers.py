"""Serializers for user authentication and registration."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import serializers

from .models import Organization, SURVEY_ADMIN_GROUP, SURVEY_ANALYST_GROUP, SURVEY_VIEWER_GROUP

User = get_user_model()


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization."""
    
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = ["id", "name", "description", "is_active", "user_count", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def get_user_count(self, obj):
        return obj.users.count()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for client registration."""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "password_confirm"]
        read_only_fields = ["id"]
    
    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"]
        )
        # No organization or group assignment during self-registration
        return user


class UserManagementSerializer(serializers.ModelSerializer):
    """Serializer for admin to create/manage users within their organization."""
    
    password = serializers.CharField(write_only=True, min_length=8, required=False)
    role = serializers.ChoiceField(
        choices=[
            (SURVEY_ADMIN_GROUP, "Admin"),
            (SURVEY_ANALYST_GROUP, "Analyst"),
            (SURVEY_VIEWER_GROUP, "Viewer")
        ],
        write_only=True,
        required=False
    )
    
    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "password", "role", "organization", "groups", "is_active", "date_joined"
        ]
        read_only_fields = ["id", "date_joined", "groups"]
    
    def create(self, validated_data):
        role = validated_data.pop("role", None)
        password = validated_data.pop("password")
        
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=password,
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            organization=validated_data.get("organization")
        )
        
        # Assign role/group if provided
        if role:
            group, _ = Group.objects.get_or_create(name=role)
            user.groups.add(group)
        
        return user
    
    def update(self, instance, validated_data):
        role = validated_data.pop("role", None)
        password = validated_data.pop("password", None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update password if provided
        if password:
            instance.set_password(password)
        
        # Update role if provided
        if role:
            instance.groups.clear()
            group, _ = Group.objects.get_or_create(name=role)
            instance.groups.add(group)
        
        instance.save()
        return instance


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile."""
    
    groups = serializers.StringRelatedField(many=True, read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    
    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "organization", "organization_name", "groups", "is_active", "date_joined"
        ]
        read_only_fields = ["id", "date_joined", "organization"]


class LoginSerializer(serializers.Serializer):
    """Serializer for login credentials."""
    
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
