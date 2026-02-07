"""Property-based tests for model routing based on capabilities.

**Property 2: Model Routing Based on Capabilities**
**Validates: Requirements 1.2, 4.5**
Test that subtasks are routed to models with matching capabilities
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import sys
import os

# Add ai_council to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from ai_council.core.models import TaskType
from app.services.cloud_ai.model_registry import (
    MODEL_REGISTRY,
    get_models_for_task_type,
    get_cheapest_model_for_task,
    get_fastest_model_for_task,
    get_best_quality_model_for_task,
)


class TestModelRouting:
    """Test that models are correctly routed based on task capabilities."""
    
    @given(
        task_type=st.sampled_from([
            TaskType.REASONING,
            TaskType.RESEARCH,
            TaskType.CODE_GENERATION,
            TaskType.DEBUGGING,
            TaskType.CREATIVE_OUTPUT,
            TaskType.FACT_CHECKING,
        ])
    )
    @settings(max_examples=50, deadline=None)
    def test_models_have_matching_capabilities(self, task_type):
        """Property: All models returned for a task type support that task type.
        
        This test verifies that:
        1. get_models_for_task_type only returns models with the requested capability
        2. Each returned model has the task_type in its capabilities list
        """
        # Get models for this task type
        models = get_models_for_task_type(task_type)
        
        # If no models support this task type, that's valid (skip test)
        assume(len(models) > 0)
        
        # Verify each model has the capability
        for model_id in models:
            config = MODEL_REGISTRY[model_id]
            assert task_type in config["capabilities"], \
                f"Model {model_id} returned for {task_type} but doesn't have that capability"
    
    @given(
        task_type=st.sampled_from([
            TaskType.REASONING,
            TaskType.RESEARCH,
            TaskType.CODE_GENERATION,
            TaskType.CREATIVE_OUTPUT,
        ])
    )
    @settings(max_examples=30, deadline=None)
    def test_cheapest_model_is_actually_cheapest(self, task_type):
        """Property: The cheapest model for a task type has the lowest cost.
        
        This test verifies that:
        1. get_cheapest_model_for_task returns a model with the task capability
        2. No other model with the same capability has lower cost
        """
        # Get all models for this task type
        models = get_models_for_task_type(task_type)
        assume(len(models) > 0)
        
        # Get the cheapest model
        cheapest = get_cheapest_model_for_task(task_type)
        
        # Verify it's in the list
        assert cheapest in models, f"Cheapest model {cheapest} not in models list"
        
        # Calculate its cost
        cheapest_config = MODEL_REGISTRY[cheapest]
        cheapest_cost = (
            cheapest_config["cost_per_input_token"] +
            cheapest_config["cost_per_output_token"]
        )
        
        # Verify no other model is cheaper
        for model_id in models:
            config = MODEL_REGISTRY[model_id]
            model_cost = (
                config["cost_per_input_token"] +
                config["cost_per_output_token"]
            )
            assert model_cost >= cheapest_cost, \
                f"Model {model_id} has lower cost than 'cheapest' model {cheapest}"
    
    @given(
        task_type=st.sampled_from([
            TaskType.REASONING,
            TaskType.RESEARCH,
            TaskType.CODE_GENERATION,
            TaskType.CREATIVE_OUTPUT,
        ])
    )
    @settings(max_examples=30, deadline=None)
    def test_fastest_model_is_actually_fastest(self, task_type):
        """Property: The fastest model for a task type has the lowest latency.
        
        This test verifies that:
        1. get_fastest_model_for_task returns a model with the task capability
        2. No other model with the same capability has lower latency
        """
        # Get all models for this task type
        models = get_models_for_task_type(task_type)
        assume(len(models) > 0)
        
        # Get the fastest model
        fastest = get_fastest_model_for_task(task_type)
        
        # Verify it's in the list
        assert fastest in models, f"Fastest model {fastest} not in models list"
        
        # Get its latency
        fastest_latency = MODEL_REGISTRY[fastest]["average_latency"]
        
        # Verify no other model is faster
        for model_id in models:
            model_latency = MODEL_REGISTRY[model_id]["average_latency"]
            assert model_latency >= fastest_latency, \
                f"Model {model_id} has lower latency than 'fastest' model {fastest}"
    
    @given(
        task_type=st.sampled_from([
            TaskType.REASONING,
            TaskType.RESEARCH,
            TaskType.CODE_GENERATION,
            TaskType.CREATIVE_OUTPUT,
        ])
    )
    @settings(max_examples=30, deadline=None)
    def test_best_quality_model_has_highest_reliability(self, task_type):
        """Property: The best quality model has the highest reliability score.
        
        This test verifies that:
        1. get_best_quality_model_for_task returns a model with the task capability
        2. No other model with the same capability has higher reliability
        """
        # Get all models for this task type
        models = get_models_for_task_type(task_type)
        assume(len(models) > 0)
        
        # Get the best quality model
        best = get_best_quality_model_for_task(task_type)
        
        # Verify it's in the list
        assert best in models, f"Best quality model {best} not in models list"
        
        # Get its reliability score
        best_reliability = MODEL_REGISTRY[best]["reliability_score"]
        
        # Verify no other model has higher reliability
        for model_id in models:
            model_reliability = MODEL_REGISTRY[model_id]["reliability_score"]
            assert model_reliability <= best_reliability, \
                f"Model {model_id} has higher reliability than 'best' model {best}"
    
    def test_all_models_have_required_fields(self):
        """Test that all models in registry have required configuration fields."""
        required_fields = [
            "provider",
            "model_name",
            "capabilities",
            "cost_per_input_token",
            "cost_per_output_token",
            "average_latency",
            "max_context",
            "reliability_score",
        ]
        
        for model_id, config in MODEL_REGISTRY.items():
            for field in required_fields:
                assert field in config, \
                    f"Model {model_id} missing required field: {field}"
            
            # Verify capabilities is a list
            assert isinstance(config["capabilities"], list), \
                f"Model {model_id} capabilities should be a list"
            
            # Verify all capabilities are TaskType enums
            for cap in config["capabilities"]:
                assert isinstance(cap, TaskType), \
                    f"Model {model_id} has invalid capability: {cap}"
    
    def test_model_registry_coverage(self):
        """Test that model registry covers all major task types."""
        important_task_types = [
            TaskType.REASONING,
            TaskType.RESEARCH,
            TaskType.CODE_GENERATION,
            TaskType.CREATIVE_OUTPUT,
        ]
        
        for task_type in important_task_types:
            models = get_models_for_task_type(task_type)
            assert len(models) > 0, \
                f"No models available for important task type: {task_type}"
    
    @given(
        task_type=st.sampled_from([
            TaskType.REASONING,
            TaskType.RESEARCH,
            TaskType.CODE_GENERATION,
            TaskType.CREATIVE_OUTPUT,
        ])
    )
    @settings(max_examples=20, deadline=None)
    def test_routing_functions_return_valid_model_ids(self, task_type):
        """Property: All routing functions return valid model IDs from the registry.
        
        This test verifies that:
        1. Routing functions return model IDs that exist in MODEL_REGISTRY
        2. The returned models have the requested capability
        """
        models = get_models_for_task_type(task_type)
        assume(len(models) > 0)
        
        # Test cheapest
        cheapest = get_cheapest_model_for_task(task_type)
        assert cheapest in MODEL_REGISTRY, f"Cheapest model {cheapest} not in registry"
        assert task_type in MODEL_REGISTRY[cheapest]["capabilities"]
        
        # Test fastest
        fastest = get_fastest_model_for_task(task_type)
        assert fastest in MODEL_REGISTRY, f"Fastest model {fastest} not in registry"
        assert task_type in MODEL_REGISTRY[fastest]["capabilities"]
        
        # Test best quality
        best = get_best_quality_model_for_task(task_type)
        assert best in MODEL_REGISTRY, f"Best quality model {best} not in registry"
        assert task_type in MODEL_REGISTRY[best]["capabilities"]
