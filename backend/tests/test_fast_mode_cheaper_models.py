"""
Property Test: FAST Mode Uses Cheaper Models

Property 18: FAST Mode Uses Cheaper Models
Validates: Requirements 5.4, 5.6

Test that FAST execution mode uses models with lower cost_per_token compared to BEST_QUALITY mode.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import ai_council
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from hypothesis import given, strategies as st, settings
from ai_council.core.models import ExecutionMode
from app.services.execution_mode_config import get_execution_mode_config, get_model_preferences_for_mode
from app.services.cloud_ai.model_registry import MODEL_REGISTRY


@pytest.mark.property(
    feature="web-application-deployment",
    property=18,
    text="FAST Mode Uses Cheaper Models"
)
@given(
    # Generate random model selections to test the property holds
    fast_model_index=st.integers(min_value=0, max_value=2),  # FAST has 3 preferred models
    best_model_index=st.integers(min_value=0, max_value=3)   # BEST_QUALITY has 4 preferred models
)
@settings(
    max_examples=100,
    deadline=1000,  # 1 second per example
)
def test_fast_mode_uses_cheaper_models_property(fast_model_index, best_model_index):
    """
    Property 18: For any model selection, FAST mode should prefer models with
    lower average cost_per_token compared to BEST_QUALITY mode.
    
    This validates that FAST mode prioritizes cost-effectiveness as specified in the requirements.
    """
    # Get preferred models for each execution mode
    fast_models = get_model_preferences_for_mode(ExecutionMode.FAST)
    best_models = get_model_preferences_for_mode(ExecutionMode.BEST_QUALITY)
    
    # Ensure we have models configured
    assert len(fast_models) > 0, "FAST mode should have preferred models configured"
    assert len(best_models) > 0, "BEST_QUALITY mode should have preferred models configured"
    
    # Get a sample model from each mode's preferences
    fast_model_id = fast_models[fast_model_index % len(fast_models)]
    best_model_id = best_models[best_model_index % len(best_models)]
    
    # Get model configurations
    fast_model_config = MODEL_REGISTRY.get(fast_model_id)
    best_model_config = MODEL_REGISTRY.get(best_model_id)
    
    # Skip if models not found in registry (configuration issue)
    if not fast_model_config or not best_model_config:
        return
    
    # Calculate average cost per token for each model
    fast_avg_cost = (
        fast_model_config["cost_per_input_token"] + 
        fast_model_config["cost_per_output_token"]
    ) / 2
    
    best_avg_cost = (
        best_model_config["cost_per_input_token"] + 
        best_model_config["cost_per_output_token"]
    ) / 2
    
    # Property: The average cost of FAST mode's preferred models should be
    # lower than or equal to BEST_QUALITY mode's preferred models
    # We check this by verifying that FAST mode includes at least some cheaper models
    
    # Get all costs for FAST mode models
    fast_costs = []
    for model_id in fast_models:
        if model_id in MODEL_REGISTRY:
            config = MODEL_REGISTRY[model_id]
            avg_cost = (config["cost_per_input_token"] + config["cost_per_output_token"]) / 2
            fast_costs.append(avg_cost)
    
    # Get all costs for BEST_QUALITY mode models
    best_costs = []
    for model_id in best_models:
        if model_id in MODEL_REGISTRY:
            config = MODEL_REGISTRY[model_id]
            avg_cost = (config["cost_per_input_token"] + config["cost_per_output_token"]) / 2
            best_costs.append(avg_cost)
    
    # Verify FAST mode has cheaper options
    if fast_costs and best_costs:
        # The minimum cost in FAST mode should be lower than or equal to minimum in BEST_QUALITY
        min_fast_cost = min(fast_costs)
        min_best_cost = min(best_costs)
        
        assert min_fast_cost <= min_best_cost, (
            f"FAST mode should have cheaper model options. "
            f"Min FAST cost=${min_fast_cost:.8f}, Min BEST_QUALITY cost=${min_best_cost:.8f}"
        )
        
        # The average cost across FAST mode models should be lower than BEST_QUALITY
        avg_fast_cost = sum(fast_costs) / len(fast_costs)
        avg_best_cost = sum(best_costs) / len(best_costs)
        
        assert avg_fast_cost <= avg_best_cost, (
            f"FAST mode should have lower average model cost. "
            f"Avg FAST cost=${avg_fast_cost:.8f}, Avg BEST_QUALITY cost=${avg_best_cost:.8f}"
        )


def test_fast_mode_cheaper_models_configuration():
    """
    Unit test to verify FAST mode is configured with cheaper models.
    
    This test validates the model preferences in execution mode configuration.
    """
    # Get preferred models for each mode
    fast_models = get_model_preferences_for_mode(ExecutionMode.FAST)
    balanced_models = get_model_preferences_for_mode(ExecutionMode.BALANCED)
    best_models = get_model_preferences_for_mode(ExecutionMode.BEST_QUALITY)
    
    print("\nModel preferences by execution mode:")
    print(f"  FAST: {fast_models}")
    print(f"  BALANCED: {balanced_models}")
    print(f"  BEST_QUALITY: {best_models}")
    
    # Calculate average costs for each mode
    def get_average_cost(model_list):
        costs = []
        for model_id in model_list:
            if model_id in MODEL_REGISTRY:
                config = MODEL_REGISTRY[model_id]
                avg_cost = (config["cost_per_input_token"] + config["cost_per_output_token"]) / 2
                costs.append(avg_cost)
        return sum(costs) / len(costs) if costs else 0
    
    fast_avg_cost = get_average_cost(fast_models)
    balanced_avg_cost = get_average_cost(balanced_models)
    best_avg_cost = get_average_cost(best_models)
    
    print(f"\nAverage cost per token:")
    print(f"  FAST: ${fast_avg_cost:.8f}")
    print(f"  BALANCED: ${balanced_avg_cost:.8f}")
    print(f"  BEST_QUALITY: ${best_avg_cost:.8f}")
    
    # Verify cost progression: FAST <= BALANCED <= BEST_QUALITY
    assert fast_avg_cost <= balanced_avg_cost, (
        f"FAST mode should have lower or equal average cost than BALANCED. "
        f"FAST=${fast_avg_cost:.8f}, BALANCED=${balanced_avg_cost:.8f}"
    )
    
    assert balanced_avg_cost <= best_avg_cost, (
        f"BALANCED mode should have lower or equal average cost than BEST_QUALITY. "
        f"BALANCED=${balanced_avg_cost:.8f}, BEST_QUALITY=${best_avg_cost:.8f}"
    )
    
    # Verify FAST mode includes cost-effective models
    fast_model_names = [MODEL_REGISTRY[m]["model_name"] for m in fast_models if m in MODEL_REGISTRY]
    print(f"\nFAST mode models: {fast_model_names}")
    
    # Check that FAST mode prefers specific cheap models
    cheap_model_keywords = ["mixtral-8x7b", "mistral-7b"]
    has_cheap_model = any(
        any(keyword in model_name.lower() for keyword in cheap_model_keywords)
        for model_name in fast_model_names
    )
    
    assert has_cheap_model, (
        f"FAST mode should include cost-effective models like Mixtral-8x7B or Mistral-7B. "
        f"Got: {fast_model_names}"
    )


def test_fast_mode_excludes_premium_models():
    """
    Test that FAST mode does not prioritize premium expensive models.
    """
    fast_models = get_model_preferences_for_mode(ExecutionMode.FAST)
    
    # Premium models that should not be in FAST mode's top preferences
    premium_keywords = ["claude-3-sonnet", "gpt-4-turbo", "gpt4"]
    
    fast_model_names = [
        MODEL_REGISTRY[m]["model_name"].lower() 
        for m in fast_models 
        if m in MODEL_REGISTRY
    ]
    
    print(f"\nFAST mode model names: {fast_model_names}")
    
    # Check that premium models are not in FAST mode preferences
    for model_name in fast_model_names:
        for premium_keyword in premium_keywords:
            assert premium_keyword not in model_name, (
                f"FAST mode should not prioritize premium model '{model_name}' "
                f"containing '{premium_keyword}'"
            )
    
    print("✓ FAST mode correctly excludes premium models from preferences")


def test_best_quality_mode_includes_premium_models():
    """
    Test that BEST_QUALITY mode includes premium high-quality models.
    """
    best_models = get_model_preferences_for_mode(ExecutionMode.BEST_QUALITY)
    
    # Premium models that should be in BEST_QUALITY mode
    premium_keywords = ["claude", "gpt-4", "gpt4", "llama3-70b"]
    
    best_model_names = [
        MODEL_REGISTRY[m]["model_name"].lower() 
        for m in best_models 
        if m in MODEL_REGISTRY
    ]
    
    print(f"\nBEST_QUALITY mode model names: {best_model_names}")
    
    # Check that at least one premium model is in BEST_QUALITY mode preferences
    has_premium_model = any(
        any(keyword in model_name for keyword in premium_keywords)
        for model_name in best_model_names
    )
    
    assert has_premium_model, (
        f"BEST_QUALITY mode should include premium models like Claude, GPT-4, or Llama3-70B. "
        f"Got: {best_model_names}"
    )
    
    print("✓ BEST_QUALITY mode correctly includes premium models")


def test_model_cost_comparison_detailed():
    """
    Detailed test comparing model costs across execution modes.
    """
    print("\n" + "="*80)
    print("DETAILED MODEL COST COMPARISON")
    print("="*80)
    
    for mode in [ExecutionMode.FAST, ExecutionMode.BALANCED, ExecutionMode.BEST_QUALITY]:
        models = get_model_preferences_for_mode(mode)
        print(f"\n{mode.value.upper()} MODE:")
        print("-" * 80)
        
        for model_id in models:
            if model_id in MODEL_REGISTRY:
                config = MODEL_REGISTRY[model_id]
                avg_cost = (config["cost_per_input_token"] + config["cost_per_output_token"]) / 2
                print(f"  {model_id:40s} ${avg_cost:.8f} per token")
                print(f"    Input: ${config['cost_per_input_token']:.8f}, "
                      f"Output: ${config['cost_per_output_token']:.8f}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    # Run all tests
    test_fast_mode_cheaper_models_configuration()
    test_fast_mode_excludes_premium_models()
    test_best_quality_mode_includes_premium_models()
    test_model_cost_comparison_detailed()
