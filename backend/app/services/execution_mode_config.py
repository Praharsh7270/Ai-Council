"""
Execution Mode Configuration for AI Council Web Application.

This module defines execution mode parameters that control how AI Council
processes requests with different speed/cost/quality trade-offs.
"""

from typing import Dict, List
from ai_council.core.models import ExecutionMode
from ai_council.utils.config import ExecutionModeConfig


# Execution mode configurations
# These control decomposition depth, model selection, and orchestration behavior
EXECUTION_MODE_CONFIGS: Dict[str, ExecutionModeConfig] = {
    # FAST mode: minimal decomposition, cheaper models, faster response
    "fast": ExecutionModeConfig(
        mode=ExecutionMode.FAST,
        max_parallel_executions=3,  # Limit parallelism to reduce overhead
        timeout_seconds=30.0,  # Shorter timeout for faster response
        max_retries=1,  # Minimal retries
        enable_arbitration=False,  # Skip arbitration to save time
        enable_synthesis=True,  # Still synthesize results
        accuracy_requirement=0.7,  # Lower accuracy threshold
        cost_limit=1.0,  # Strict cost limit ($1.00)
        preferred_model_types=[
            "groq-mixtral-8x7b",  # Fast and cheap
            "huggingface-mistral-7b",  # Cost-effective
            "together-mixtral-8x7b"  # Backup fast option
        ],
        fallback_strategy="cheapest"  # Always prefer cheapest model
    ),
    
    # BALANCED mode: moderate decomposition, mixed models, balanced approach
    "balanced": ExecutionModeConfig(
        mode=ExecutionMode.BALANCED,
        max_parallel_executions=5,  # Moderate parallelism
        timeout_seconds=60.0,  # Standard timeout
        max_retries=3,  # Standard retries
        enable_arbitration=True,  # Enable arbitration for conflicts
        enable_synthesis=True,  # Full synthesis
        accuracy_requirement=0.8,  # Standard accuracy
        cost_limit=5.0,  # Moderate cost limit ($5.00)
        preferred_model_types=[
            "groq-llama3-70b",  # Good balance of speed and quality
            "together-mixtral-8x7b",  # Versatile model
            "groq-mixtral-8x7b",  # Fast backup
            "together-llama2-70b"  # Quality backup
        ],
        fallback_strategy="automatic"  # Automatic fallback selection
    ),
    
    # BEST_QUALITY mode: maximum decomposition, premium models, highest quality
    "best_quality": ExecutionModeConfig(
        mode=ExecutionMode.BEST_QUALITY,
        max_parallel_executions=8,  # Maximum parallelism
        timeout_seconds=120.0,  # Extended timeout for complex processing
        max_retries=5,  # Maximum retries for reliability
        enable_arbitration=True,  # Full arbitration for conflicts
        enable_synthesis=True,  # Comprehensive synthesis
        accuracy_requirement=0.95,  # Highest accuracy requirement
        cost_limit=None,  # No cost limit - prioritize quality
        preferred_model_types=[
            "openrouter-claude-3-sonnet",  # Premium model for best quality
            "openrouter-gpt4-turbo",  # Alternative premium model
            "groq-llama3-70b",  # High-quality backup
            "together-llama2-70b"  # Additional quality option
        ],
        fallback_strategy="highest_quality"  # Always prefer highest quality
    )
}


def get_execution_mode_config(execution_mode: ExecutionMode) -> ExecutionModeConfig:
    """
    Get the configuration for a specific execution mode.
    
    Args:
        execution_mode: The execution mode enum value
        
    Returns:
        ExecutionModeConfig: Configuration for the specified mode
        
    Raises:
        ValueError: If execution mode is not recognized
    """
    mode_key = execution_mode.value.lower()
    
    if mode_key not in EXECUTION_MODE_CONFIGS:
        raise ValueError(f"Unknown execution mode: {execution_mode.value}")
    
    return EXECUTION_MODE_CONFIGS[mode_key]


def get_model_preferences_for_mode(execution_mode: ExecutionMode) -> List[str]:
    """
    Get the preferred model list for a specific execution mode.
    
    Args:
        execution_mode: The execution mode enum value
        
    Returns:
        List of preferred model IDs in priority order
    """
    config = get_execution_mode_config(execution_mode)
    return config.preferred_model_types


def should_enable_arbitration(execution_mode: ExecutionMode) -> bool:
    """
    Check if arbitration should be enabled for a specific execution mode.
    
    Args:
        execution_mode: The execution mode enum value
        
    Returns:
        True if arbitration should be enabled, False otherwise
    """
    config = get_execution_mode_config(execution_mode)
    return config.enable_arbitration


def get_max_parallel_executions(execution_mode: ExecutionMode) -> int:
    """
    Get the maximum number of parallel executions for a specific execution mode.
    
    Args:
        execution_mode: The execution mode enum value
        
    Returns:
        Maximum number of parallel executions
    """
    config = get_execution_mode_config(execution_mode)
    return config.max_parallel_executions


def get_accuracy_requirement(execution_mode: ExecutionMode) -> float:
    """
    Get the accuracy requirement for a specific execution mode.
    
    Args:
        execution_mode: The execution mode enum value
        
    Returns:
        Accuracy requirement (0.0 to 1.0)
    """
    config = get_execution_mode_config(execution_mode)
    return config.accuracy_requirement


def get_cost_limit(execution_mode: ExecutionMode) -> float:
    """
    Get the cost limit for a specific execution mode.
    
    Args:
        execution_mode: The execution mode enum value
        
    Returns:
        Cost limit in USD, or None if no limit
    """
    config = get_execution_mode_config(execution_mode)
    return config.cost_limit


# Export configuration summary for documentation
EXECUTION_MODE_SUMMARY = {
    "fast": {
        "description": "Minimal decomposition, cheaper models, faster response",
        "use_case": "Quick queries, simple tasks, cost-sensitive operations",
        "characteristics": {
            "decomposition": "minimal",
            "models": "cheaper (Mixtral-8x7B, Mistral-7B)",
            "arbitration": "disabled",
            "parallelism": "limited (3 concurrent)",
            "accuracy": "0.7 (good)",
            "cost_limit": "$1.00",
            "timeout": "30 seconds"
        }
    },
    "balanced": {
        "description": "Moderate decomposition, mixed models, balanced approach",
        "use_case": "General purpose, standard queries, balanced cost/quality",
        "characteristics": {
            "decomposition": "moderate",
            "models": "mixed (Llama3-70B, Mixtral-8x7B)",
            "arbitration": "enabled",
            "parallelism": "moderate (5 concurrent)",
            "accuracy": "0.8 (very good)",
            "cost_limit": "$5.00",
            "timeout": "60 seconds"
        }
    },
    "best_quality": {
        "description": "Maximum decomposition, premium models, highest quality",
        "use_case": "Complex tasks, critical decisions, quality-first operations",
        "characteristics": {
            "decomposition": "maximum",
            "models": "premium (Claude-3-Sonnet, GPT-4-Turbo, Llama3-70B)",
            "arbitration": "enabled",
            "parallelism": "maximum (8 concurrent)",
            "accuracy": "0.95 (excellent)",
            "cost_limit": "none (quality prioritized)",
            "timeout": "120 seconds"
        }
    }
}
