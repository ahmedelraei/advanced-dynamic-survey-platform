from django.contrib import admin

from .models import Field, Section, Survey


class SectionInline(admin.TabularInline):
    model = Section
    extra = 0
    fields = ("title", "order", "logic_rules")


class FieldInline(admin.TabularInline):
    model = Field
    extra = 0
    fields = ("label", "field_type", "is_required", "order", "is_sensitive")


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "is_active", "version", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "description", "owner__email")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [SectionInline]


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("title", "survey", "order")
    list_filter = ("survey",)
    search_fields = ("title",)
    inlines = [FieldInline]


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ("label", "section", "field_type", "is_required", "is_sensitive", "order")
    list_filter = ("field_type", "is_required", "is_sensitive")
    search_fields = ("label",)
