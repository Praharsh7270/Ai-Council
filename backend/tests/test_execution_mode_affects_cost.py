"""
Property Test: Execution Mode Affects Total Cost

Property 19: Execution Mode Affects Total Cost
Validates: Requirements 5.4, 5.5, 5.6

Test that cost_fast ≤ cost_balanced ≤ cost_best_quality for any identical request.
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
    property=19,
    text="Execution Mode Affects Total Cost"
)
@given(
    # Simulate token usage for a request
    input_tokens=st.integers(min_value=100, max_value=2000),
    output_tokens=st.integers(min_value=50, max_value=1000),
    # Simulate number of subtasks (FAST has fewer, BEST_QUALITY has more)
    fast_subtasks=st.integers(min_value=1, max_value=3),
    balanced_subtasks=st.integers(min_value=2, max_value=5),
    best_subtasks=st.integers(min_value=3, max_value=8)
)
@settings(
    max_examples=100,
    deadline=2000,  # 2 seconds per example
)
def test_execution_mode_affects_cost_property(
    input_tokens, 
    output_tokens, 
    fast_subtasks, 
    balanced_subtasks, 
    best_subtasks
):
    """
    Property 19: For any identical request processed in different execution modes,
    the total costs should satisfy: cost_fast ≤ cost_balanced ≤ cost_best_quality.
    
    This validates that execution mode selection affects cost as specified in the requirements.
    """
    # Ensure subtask counts follow the expected pattern
    # FAST should have fewer or equal subtasks than BALANCED
    # BALANCED should have fewer or equal subtasks than BEST_QUALITY
    if fast_subtasks > balanced_subtasks:
        fast_subtasks = balanced_subtasks
    if balanced_subtasks > best_subtasks:
        balanced_subtasks = best_subtasks
    
    # Calculate estimated cost for each execution mode
    def calculate_mode_cost(execution_mode, num_subtasks, input_tokens, output_tokens):
        """Calculate estimated cost for a given execution mode."""
        # Get preferred models for this mode
        preferred_models = get_model_preferences_for_mode(execution_mode)
        
        if not preferred_models:
            return 0.0
        
        # Use the first preferred model as representative
        model_id = preferred_models[0]
        
        if model_id not in MODEL_REGISTRY:
            return 0.0
        
        model_config = MODEL_REGISTRY[model_id]
        
        # Calculate cost per subtask
        cost_per_subtask = (
            input_tokens * model_config["cost_per_input_token"] +
            output_tokens * model_config["cost_per_output_token"]
        )
        
        # Total cost = cost per subtask × number of subtasks
        total_cost = cost_per_subtask * num_subtasks
        
        return total_cost
    
    # Calculate costs for each mode
    cost_fast = calculate_mode_cost(ExecutionMode.FAST, fast_subtasks, input_tokens, output_tokens)
    cost_balanced = calculate_mode_cost(ExecutionMode.BALANCED, balanced_subtasks, input_tokens, output_tokens)
    cost_best = calculate_mode_cost(ExecutionMode.BEST_QUALITY, best_subtasks, input_tokens, output_tokens)
    
    # Verify property: cost_fast ≤ cost_balanced ≤ cost_best_quality
    assert cost_fast <= cost_balanced, (
        f"FAST mode cost should be ≤ BALANCED mode cost. "
        f"FAST=${cost_fast:.6f}, BALANCED=${cost_balanced:.6f}"
    )
    
    assert cost_balanced <= cost_best, (
        f"BALANCED mode cost should be ≤ BEST_QUALITY mode cost. "
        f"BALANCED=${cost_balanced:.6f}, BEST_QUALITY=${cost_best:.6f}"
    )


def test_execution_mode_cost_comparison_example():
    """
    Example test showing cost differences across execution modes.
    """
    # Simulate a typical request
    input_tokens = 500
    output_tokens = 300
    
    # Typical subtask counts for each mode
    fast_subtasks = 2
    balanced_subtasks = 4
    best_subtasks = 6
    
    print("\n" + "="*80)
    print("EXECUTION MODE COST COMPARISON")
    print("="*80)
    print(f"Request: {input_tokens} input tokens, {output_tokens} output tokens")
    print()
    
    for mode, num_subtasks in [
        (ExecutionMode.FAST, fast_subtasks),
        (ExecutionMode.BALANCED, balanced_subtasks),
        (ExecutionMode.BEST_QUALITY, best_subtasks)
    ]:
        preferred_models = get_model_preferences_for_mode(mode)
        model_id = preferred_models[0] if preferred_models else None
        
        if model_id and model_id in MODEL_REGISTRY:
            model_config = MODEL_REGISTRY[model_id]
            
            # Calculate cost per subtask
            cost_per_subtask = (
                input_tokens * model_config["cost_per_input_token"] +
                output_tokens * model_config["cost_per_output_token"]
            )
            
            # Total cost
            total_cost = cost_per_subtask * num_subtasks
            
            print(f"{mode.value.upper()} MODE:")
            print(f"  Primary model: {model_id}")
            print(f"  Subtasks: {num_subtasks}")
            print(f"  Cost per subtask: ${cost_per_subtask:.6f}")
            print(f"  Total cost: ${total_cost:.6f}")
            print()
    
    print("="*80)


def test_cost_progression_with_config_limits():
    """
    Test that cost limits in configuration support the cost progression property.
    """
    fast_config = get_execution_mode_config(ExecutionMode.FAST)
    balanced_config = get_execution_mode_config(ExecutionMode.BALANCED)
    best_config = get_execution_mode_config(ExecutionMode.BEST_QUALITY)
    
    print("\nCost limits by execution mode:")
    print(f"  FAST: ${fast_config.cost_limit if fast_config.cost_limit else 'unlimited'}")
    print(f"  BALANCED: ${balanced_config.cost_limit if balanced_config.cost_limit else 'unlimited'}")
    print(f"  BEST_QUALITY: ${best_config.cost_limit if best_config.cost_limit else 'unlimited'}")
    
    # Verify cost limit progression
    if fast_config.cost_limit is not None and balanced_config.cost_limit is not None:
        assert fast_config.cost_limit <= balanced_config.cost_limit, (
            f"FAST mode cost limit should be ≤ BALANCED mode cost limit. "
            f"FAST=${fast_config.cost_limit}, BALANCED=${balanced_config.cost_limit}"
        )
    
    # FAST mode should have a strict cost limit
    assert fast_config.cost_limit is not None, "FAST mode should have a cost limit"
    assert fast_config.cost_limit < 5.0, (
        f"FAST mode should have a strict cost limit (< $5.00), got ${fast_config.cost_limit}"
    )
    
    # BEST_QUALITY mode may not have a cost limit (prioritizes quality)
    if best_config.cost_limit is None:
        print("  ✓ BEST_QUALITY mode has no cost limit (quality prioritized)")
    
    print("\n✓ Cost limit configuration supports cost progression property")


def test_model_cost_affects_total_cost():
    """
    Test that using cheaper models in FAST mode leads to lower total costs.
    """
    # Get average model costs for each mode
    def get_average_model_cost(execution_mode):
        """Get average cost per token for models in this execution mode."""
        preferred_models = get_model_preferences_for_mode(execution_mode)
        
        costs = []
        for model_id in preferred_models:
            if model_id in MODEL_REGISTRY:
                config = MODEL_REGISTRY[model_id]
                avg_cost = (config["cost_per_input_token"] + config["cost_per_output_token"]) / 2
                costs.append(avg_cost)
        
        return sum(costs) / len(costs) if costs else 0
    
    fast_avg_cost = get_average_model_cost(ExecutionMode.FAST)
    balanced_avg_cost = get_average_model_cost(ExecutionMode.BALANCED)
    best_avg_cost = get_average_model_cost(ExecutionMode.BEST_QUALITY)
    
    print("\nAverage model cost per token:")
    print(f"  FAST: ${fast_avg_cost:.8f}")
    print(f"  BALANCED: ${balanced_avg_cost:.8f}")
    print(f"  BEST_QUALITY: ${best_avg_cost:.8f}")
    
    # Verify cost progression
    assert fast_avg_cost <= balanced_avg_cost, (
        f"FAST mode average model cost should be ≤ BALANCED. "
        f"FAST=${fast_avg_cost:.8f}, BALANCED=${balanced_avg_cost:.8f}"
    )
    
    assert balanced_avg_cost <= best_avg_cost, (
        f"BALANCED mode average model cost should be ≤ BEST_QUALITY. "
        f"BALANCED=${balanced_avg_cost:.8f}, BEST_QUALITY=${best_avg_cost:.8f}"
    )
    
    # Calculate cost multiplier
    fast_to_best_multiplier = best_avg_cost / fast_avg_cost if fast_avg_cost > 0 else 0
    
    print(f"\nCost multiplier (BEST_QUALITY / FAST): {fast_to_best_multiplier:.2f}x")
    print(f"  BEST_QUALITY mode costs ~{fast_to_best_multiplier:.1f}x more per token than FAST mode")
    
    print("\n✓ Model cost progression supports total cost property")


def test_combined_factors_affect_total_cost():
    """
    Test that both model cost and subtask count combine to affect total cost.
    """
    # Simulate a request with typical token counts
    input_tokens = 1000
    output_tokens = 500
    
    print("\n" + "="*80)
    print("COMBINED FACTORS AFFECTING TOTAL COST")
    print("="*80)
    print(f"Request: {input_tokens} input tokens, {output_tokens} output tokens\n")
    
    # Define typical subtask counts
    mode_configs = [
        (ExecutionMode.FAST, 2, "Minimal decomposition"),
        (ExecutionMode.BALANCED, 4, "Moderate decomposition"),
        (ExecutionMode.BEST_QUALITY, 7, "Maximum decomposition")
    ]
    
    costs = []
    
    for mode, num_subtasks, description in mode_configs:
        preferred_models = get_model_preferences_for_mode(mode)
        model_id = preferred_models[0] if preferred_models else None
        
        if model_id and model_id in MODEL_REGISTRY:
            model_config = MODEL_REGISTRY[model_id]
            
            # Calculate cost
            cost_per_subtask = (
                input_tokens * model_config["cost_per_input_token"] +
                output_tokens * model_config["cost_per_output_token"]
            )
            total_cost = cost_per_subtask * num_subtasks
            costs.append(total_cost)
            
            print(f"{mode.value.upper()} MODE ({description}):")
            print(f"  Model: {model_id}")
            print(f"  Subtasks: {num_subtasks}")
            print(f"  Cost per subtask: ${cost_per_subtask:.6f}")
            print(f"  Total cost: ${total_cost:.6f}")
            print()
    
    # Verify cost progression
    if len(costs) == 3:
        cost_fast, cost_balanced, cost_best = costs
        
        assert cost_fast <= cost_balanced <= cost_best, (
            f"Cost progression should be FAST ≤ BALANCED ≤ BEST_QUALITY. "
            f"Got FAST=${cost_fast:.6f}, BALANCED=${cost_balanced:.6f}, BEST=${cost_best:.6f}"
        )
        
        # Calculate savings
        savings_fast_vs_best = ((cost_best - cost_fast) / cost_best * 100) if cost_best > 0 else 0
        savings_balanced_vs_best = ((cost_best - cost_balanced) / cost_best * 100) if cost_best > 0 else 0
        
        print("COST SAVINGS:")
        print(f"  FAST vs BEST_QUALITY: {savings_fast_vs_best:.1f}% cheaper")
        print(f"  BALANCED vs BEST_QUALITY: {savings_balanced_vs_best:.1f}% cheaper")
        print()
        print("="*80)
        
        print("\n✓ Combined factors (model cost + subtask count) create cost progression")


if __name__ == "__main__":
    # Run all tests
    test_execution_mode_cost_comparison_example()
    test_cost_progression_with_config_limits()
    test_model_cost_affects_total_cost()
    test_combined_factors_affect_total_cost()
