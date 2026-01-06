"""
Conditional Logic Engine for ADSP.
Maps to FR 1.2: Conditional Logic Engine.
Supports: equals, not_equals, greater_than, less_than, contains, not_contains.
"""
from enum import Enum
from typing import Any


class LogicOperator(str, Enum):
    """Supported logic operators."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUALS = "greater_than_or_equals"
    LESS_THAN_OR_EQUALS = "less_than_or_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"  # Value is in list
    NOT_IN = "not_in"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"


class LogicAction(str, Enum):
    """Actions to take when conditions are met."""
    SHOW = "show"
    HIDE = "hide"


class LogicEngine:
    """
    Evaluates conditional visibility rules for survey sections and fields.
    
    Rule Structure:
    {
        "conditions": [
            {"field_id": "uuid", "operator": "equals", "value": "USA"},
            {"field_id": "uuid2", "operator": "greater_than", "value": 18}
        ],
        "logic": "and",  # or "or"
        "action": "show"
    }
    """
    
    def __init__(self, response_data: dict):
        """
        Initialize with current response data.
        
        Args:
            response_data: Dict mapping field_id -> submitted value
        """
        self.response_data = response_data
    
    def evaluate_condition(self, condition: dict) -> bool:
        """
        Evaluate a single condition.
        
        Args:
            condition: Dict with field_id, operator, and value
            
        Returns:
            bool: Whether condition is satisfied
        """
        field_id = condition.get("field_id")
        operator = condition.get("operator")
        expected_value = condition.get("value")
        
        # Get actual value from response data
        actual_value = self.response_data.get(field_id)
        
        return self._apply_operator(operator, actual_value, expected_value)
    
    def _apply_operator(self, operator: str, actual: Any, expected: Any) -> bool:
        """Apply the specified operator to compare values."""
        
        # Handle null cases
        if operator == LogicOperator.IS_EMPTY:
            return actual is None or actual == "" or actual == []
        
        if operator == LogicOperator.IS_NOT_EMPTY:
            return actual is not None and actual != "" and actual != []
        
        # For other operators, if actual is None, condition fails
        if actual is None:
            return False
        
        # Type normalization for comparisons
        if operator in (
            LogicOperator.GREATER_THAN,
            LogicOperator.LESS_THAN,
            LogicOperator.GREATER_THAN_OR_EQUALS,
            LogicOperator.LESS_THAN_OR_EQUALS,
        ):
            try:
                actual = float(actual)
                expected = float(expected)
            except (ValueError, TypeError):
                return False
        
        # Apply operators
        if operator == LogicOperator.EQUALS:
            return str(actual).lower() == str(expected).lower()
        
        elif operator == LogicOperator.NOT_EQUALS:
            return str(actual).lower() != str(expected).lower()
        
        elif operator == LogicOperator.GREATER_THAN:
            return actual > expected
        
        elif operator == LogicOperator.LESS_THAN:
            return actual < expected
        
        elif operator == LogicOperator.GREATER_THAN_OR_EQUALS:
            return actual >= expected
        
        elif operator == LogicOperator.LESS_THAN_OR_EQUALS:
            return actual <= expected
        
        elif operator == LogicOperator.CONTAINS:
            return str(expected).lower() in str(actual).lower()
        
        elif operator == LogicOperator.NOT_CONTAINS:
            return str(expected).lower() not in str(actual).lower()
        
        elif operator == LogicOperator.IN:
            if isinstance(expected, list):
                return actual in expected
            return str(actual) in str(expected).split(",")
        
        elif operator == LogicOperator.NOT_IN:
            if isinstance(expected, list):
                return actual not in expected
            return str(actual) not in str(expected).split(",")
        
        return False
    
    def evaluate_rules(self, rules: dict) -> bool:
        """
        Evaluate a complete rule set.
        
        Args:
            rules: Dict with conditions array, logic (and/or), and action
            
        Returns:
            bool: Whether the element should be visible
        """
        if not rules or not rules.get("conditions"):
            # No rules = always visible
            return True
        
        conditions = rules.get("conditions", [])
        logic = rules.get("logic", "and").lower()
        action = rules.get("action", LogicAction.SHOW)
        
        if not conditions:
            return True
        
        # Evaluate all conditions
        results = [self.evaluate_condition(c) for c in conditions]
        
        # Apply logic
        if logic == "and":
            conditions_met = all(results)
        elif logic == "or":
            conditions_met = any(results)
        else:
            conditions_met = all(results)  # Default to AND
        
        # Apply action
        if action == LogicAction.SHOW:
            return conditions_met
        elif action == LogicAction.HIDE:
            return not conditions_met
        
        return conditions_met
    
    def get_visible_sections(self, sections: list) -> list:
        """
        Filter sections based on visibility rules.
        
        Args:
            sections: List of Section model instances
            
        Returns:
            list: Sections that should be visible
        """
        visible = []
        for section in sections:
            if self.evaluate_rules(section.logic_rules):
                visible.append(section)
        return visible
    
    def get_visible_fields(self, fields: list) -> list:
        """
        Filter fields based on visibility rules.
        
        Args:
            fields: List of Field model instances
            
        Returns:
            list: Fields that should be visible
        """
        visible = []
        for field in fields:
            if self.evaluate_rules(field.logic_rules):
                visible.append(field)
        return visible
    
    def validate_submission(self, survey, submitted_data: dict) -> tuple[bool, list[str]]:
        """
        Validate submitted data against conditional visibility.
        Ensures no data is submitted for hidden fields.
        Maps to FR 2.1: Real-time Validation.
        
        Args:
            survey: Survey model instance with prefetched sections/fields
            submitted_data: Dict of field_id -> value
            
        Returns:
            tuple: (is_valid, list of error messages)
        """
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError as DjangoValidationError
        from apps.surveys.models import FieldType
        
        errors = []
        
        for section in survey.sections.all():
            section_visible = self.evaluate_rules(section.logic_rules)
            
            for field in section.fields.all():
                field_id = str(field.id)
                field_visible = section_visible and self.evaluate_rules(field.logic_rules)
                field_value = submitted_data.get(field_id)
                
                # Check for data in hidden fields
                if not field_visible and field_value:
                    errors.append(
                        f"Field '{field.label}' should not have data (hidden by logic)"
                    )
                
                # Check required fields that are visible
                if field_visible and field.is_required:
                    if not field_value or (isinstance(field_value, str) and not field_value.strip()):
                        errors.append(f"Field '{field.label}' is required")
                
                # Validate email fields
                if field_visible and field.field_type == FieldType.EMAIL and field_value:
                    try:
                        validate_email(field_value)
                    except DjangoValidationError:
                        errors.append(f"Field '{field.label}' must be a valid email address")
                
                # Validate number fields
                if field_visible and field.field_type == FieldType.NUMBER and field_value is not None:
                    try:
                        num_value = float(field_value)
                        if field.min_value is not None and num_value < field.min_value:
                            errors.append(f"Field '{field.label}' must be at least {field.min_value}")
                        if field.max_value is not None and num_value > field.max_value:
                            errors.append(f"Field '{field.label}' must be at most {field.max_value}")
                    except (ValueError, TypeError):
                        errors.append(f"Field '{field.label}' must be a valid number")
        
        return len(errors) == 0, errors


def evaluate_cross_section_dependency(
    source_field_value: Any,
    target_options: list[dict],
    filter_key: str
) -> list[dict]:
    """
    Filter options based on cross-section dependencies.
    Maps to FR 1.3: Cross-Section Dependencies.
    
    Example: Country = "USA" filters State options to US states.
    
    Args:
        source_field_value: Value from the source field (e.g., "USA")
        target_options: List of option dicts with filters
                       [{"value": "CA", "label": "California", "filters": {"country": "USA"}}]
        filter_key: The filter key to match (e.g., "country")
        
    Returns:
        list: Filtered options
    """
    if not source_field_value:
        return target_options
    
    filtered = []
    for option in target_options:
        filters = option.get("filters", {})
        if not filters:
            # No filter = always include
            filtered.append(option)
        elif filters.get(filter_key) == source_field_value:
            filtered.append(option)
    
    return filtered
