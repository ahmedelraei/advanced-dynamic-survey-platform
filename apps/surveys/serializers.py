"""Serializers for Survey, Section, and Field."""
from rest_framework import serializers

from .models import Field, Section, Survey


class FieldSerializer(serializers.ModelSerializer):
    """Serializer for survey fields."""
    
    class Meta:
        model = Field
        fields = [
            "id", "field_type", "label", "placeholder", "help_text",
            "options", "is_required", "validation_regex", "validation_message",
            "min_value", "max_value", "logic_rules", "dependency_config",
            "is_sensitive", "order"
        ]
        read_only_fields = ["id"]


class SectionSerializer(serializers.ModelSerializer):
    """Serializer for survey sections with nested fields."""
    
    fields = FieldSerializer(many=True, read_only=True)
    
    class Meta:
        model = Section
        fields = ["id", "title", "description", "order", "logic_rules", "fields"]
        read_only_fields = ["id"]


class SurveyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for survey lists."""
    
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    section_count = serializers.IntegerField(source="sections.count", read_only=True)
    
    class Meta:
        model = Survey
        fields = [
            "id", "title", "description", "owner_email",
            "is_active", "version", "section_count", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "owner_email", "section_count", "created_at", "updated_at"]


class SurveyDetailSerializer(serializers.ModelSerializer):
    """Full serializer for survey with nested sections and fields."""
    
    sections = SectionSerializer(many=True, read_only=True)
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    
    class Meta:
        model = Survey
        fields = [
            "id", "title", "description", "owner", "owner_email",
            "is_active", "version", "sections", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "owner", "owner_email", "version", "created_at", "updated_at"]


class SurveyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating surveys with nested sections and fields."""
    
    sections = serializers.JSONField(write_only=True, required=False, default=list)
    
    class Meta:
        model = Survey
        fields = ["id", "title", "description", "is_active", "sections"]
        read_only_fields = ["id"]
    
    def create(self, validated_data):
        sections_data = validated_data.pop("sections", [])
        validated_data["owner"] = self.context["request"].user
        
        survey = Survey.objects.create(**validated_data)
        
        # Create sections and fields
        for section_order, section_data in enumerate(sections_data):
            fields_data = section_data.pop("fields", [])
            # Use order from data if provided, otherwise use enumeration
            if "order" not in section_data:
                section_data["order"] = section_order
            
            section = Section.objects.create(
                survey=survey,
                **section_data
            )
            
            for field_order, field_data in enumerate(fields_data):
                # Use order from data if provided, otherwise use enumeration
                if "order" not in field_data:
                    field_data["order"] = field_order
                
                Field.objects.create(
                    section=section,
                    **field_data
                )
        
        return survey


class SectionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating sections."""
    
    fields = serializers.JSONField(write_only=True, required=False, default=list)
    
    class Meta:
        model = Section
        fields = ["id", "title", "description", "order", "logic_rules", "fields"]
        read_only_fields = ["id"]
    
    def create(self, validated_data):
        fields_data = validated_data.pop("fields", [])
        section = Section.objects.create(**validated_data)
        
        for field_order, field_data in enumerate(fields_data):
            # Use order from data if provided, otherwise use enumeration
            if "order" not in field_data:
                field_data["order"] = field_order
            
            Field.objects.create(
                section=section,
                **field_data
            )
        
        return section

