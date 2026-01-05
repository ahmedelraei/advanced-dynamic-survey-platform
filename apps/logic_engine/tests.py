"""
Tests for the Conditional Logic Engine.
Maps to QA Plan: Unit Testing - Focus on the "Logic Engine".
"""
import pytest

from apps.logic_engine import LogicEngine, LogicOperator, evaluate_cross_section_dependency


class TestLogicOperators:
    """Test individual logic operators."""
    
    def test_equals_string(self):
        engine = LogicEngine({"field1": "USA"})
        condition = {"field_id": "field1", "operator": "equals", "value": "USA"}
        assert engine.evaluate_condition(condition) is True
    
    def test_equals_case_insensitive(self):
        engine = LogicEngine({"field1": "usa"})
        condition = {"field_id": "field1", "operator": "equals", "value": "USA"}
        assert engine.evaluate_condition(condition) is True
    
    def test_equals_false(self):
        engine = LogicEngine({"field1": "Canada"})
        condition = {"field_id": "field1", "operator": "equals", "value": "USA"}
        assert engine.evaluate_condition(condition) is False
    
    def test_not_equals(self):
        engine = LogicEngine({"field1": "Canada"})
        condition = {"field_id": "field1", "operator": "not_equals", "value": "USA"}
        assert engine.evaluate_condition(condition) is True
    
    def test_greater_than(self):
        engine = LogicEngine({"age": 25})
        condition = {"field_id": "age", "operator": "greater_than", "value": 18}
        assert engine.evaluate_condition(condition) is True
    
    def test_greater_than_false(self):
        engine = LogicEngine({"age": 15})
        condition = {"field_id": "age", "operator": "greater_than", "value": 18}
        assert engine.evaluate_condition(condition) is False
    
    def test_less_than(self):
        engine = LogicEngine({"age": 15})
        condition = {"field_id": "age", "operator": "less_than", "value": 18}
        assert engine.evaluate_condition(condition) is True
    
    def test_contains(self):
        engine = LogicEngine({"email": "user@example.com"})
        condition = {"field_id": "email", "operator": "contains", "value": "@example"}
        assert engine.evaluate_condition(condition) is True
    
    def test_contains_false(self):
        engine = LogicEngine({"email": "user@other.com"})
        condition = {"field_id": "email", "operator": "contains", "value": "@example"}
        assert engine.evaluate_condition(condition) is False
    
    def test_not_contains(self):
        engine = LogicEngine({"email": "user@other.com"})
        condition = {"field_id": "email", "operator": "not_contains", "value": "@example"}
        assert engine.evaluate_condition(condition) is True
    
    def test_is_empty_null(self):
        engine = LogicEngine({"field1": None})
        condition = {"field_id": "field1", "operator": "is_empty", "value": None}
        assert engine.evaluate_condition(condition) is True
    
    def test_is_empty_string(self):
        engine = LogicEngine({"field1": ""})
        condition = {"field_id": "field1", "operator": "is_empty", "value": None}
        assert engine.evaluate_condition(condition) is True
    
    def test_is_not_empty(self):
        engine = LogicEngine({"field1": "value"})
        condition = {"field_id": "field1", "operator": "is_not_empty", "value": None}
        assert engine.evaluate_condition(condition) is True
    
    def test_missing_field_returns_false(self):
        engine = LogicEngine({})
        condition = {"field_id": "missing", "operator": "equals", "value": "test"}
        assert engine.evaluate_condition(condition) is False
    
    def test_in_operator_list(self):
        engine = LogicEngine({"country": "USA"})
        condition = {"field_id": "country", "operator": "in", "value": ["USA", "Canada", "UK"]}
        assert engine.evaluate_condition(condition) is True
    
    def test_in_operator_false(self):
        engine = LogicEngine({"country": "Germany"})
        condition = {"field_id": "country", "operator": "in", "value": ["USA", "Canada", "UK"]}
        assert engine.evaluate_condition(condition) is False


class TestLogicRules:
    """Test complete rule evaluation."""
    
    def test_show_action_met(self):
        engine = LogicEngine({"country": "USA"})
        rules = {
            "conditions": [{"field_id": "country", "operator": "equals", "value": "USA"}],
            "logic": "and",
            "action": "show"
        }
        assert engine.evaluate_rules(rules) is True
    
    def test_show_action_not_met(self):
        engine = LogicEngine({"country": "Canada"})
        rules = {
            "conditions": [{"field_id": "country", "operator": "equals", "value": "USA"}],
            "logic": "and",
            "action": "show"
        }
        assert engine.evaluate_rules(rules) is False
    
    def test_hide_action_met(self):
        engine = LogicEngine({"country": "USA"})
        rules = {
            "conditions": [{"field_id": "country", "operator": "equals", "value": "USA"}],
            "logic": "and",
            "action": "hide"
        }
        assert engine.evaluate_rules(rules) is False  # Hidden when condition met
    
    def test_and_logic_all_true(self):
        engine = LogicEngine({"country": "USA", "age": 25})
        rules = {
            "conditions": [
                {"field_id": "country", "operator": "equals", "value": "USA"},
                {"field_id": "age", "operator": "greater_than", "value": 18}
            ],
            "logic": "and",
            "action": "show"
        }
        assert engine.evaluate_rules(rules) is True
    
    def test_and_logic_one_false(self):
        engine = LogicEngine({"country": "USA", "age": 15})
        rules = {
            "conditions": [
                {"field_id": "country", "operator": "equals", "value": "USA"},
                {"field_id": "age", "operator": "greater_than", "value": 18}
            ],
            "logic": "and",
            "action": "show"
        }
        assert engine.evaluate_rules(rules) is False
    
    def test_or_logic_one_true(self):
        engine = LogicEngine({"country": "Canada", "age": 25})
        rules = {
            "conditions": [
                {"field_id": "country", "operator": "equals", "value": "USA"},
                {"field_id": "age", "operator": "greater_than", "value": 18}
            ],
            "logic": "or",
            "action": "show"
        }
        assert engine.evaluate_rules(rules) is True
    
    def test_or_logic_none_true(self):
        engine = LogicEngine({"country": "Canada", "age": 15})
        rules = {
            "conditions": [
                {"field_id": "country", "operator": "equals", "value": "USA"},
                {"field_id": "age", "operator": "greater_than", "value": 18}
            ],
            "logic": "or",
            "action": "show"
        }
        assert engine.evaluate_rules(rules) is False
    
    def test_empty_rules_always_visible(self):
        engine = LogicEngine({})
        assert engine.evaluate_rules({}) is True
        assert engine.evaluate_rules(None) is True


class TestCrossSectionDependency:
    """Test cross-section filtering."""
    
    def test_filter_by_country(self):
        options = [
            {"value": "CA", "label": "California", "filters": {"country": "USA"}},
            {"value": "TX", "label": "Texas", "filters": {"country": "USA"}},
            {"value": "ON", "label": "Ontario", "filters": {"country": "Canada"}},
            {"value": "BC", "label": "British Columbia", "filters": {"country": "Canada"}},
        ]
        
        result = evaluate_cross_section_dependency("USA", options, "country")
        
        assert len(result) == 2
        assert result[0]["value"] == "CA"
        assert result[1]["value"] == "TX"
    
    def test_no_filter_returns_all(self):
        options = [
            {"value": "opt1", "label": "Option 1"},
            {"value": "opt2", "label": "Option 2"},
        ]
        
        result = evaluate_cross_section_dependency("USA", options, "country")
        
        assert len(result) == 2
    
    def test_empty_source_returns_all(self):
        options = [
            {"value": "CA", "label": "California", "filters": {"country": "USA"}},
        ]
        
        result = evaluate_cross_section_dependency(None, options, "country")
        
        assert len(result) == 1
