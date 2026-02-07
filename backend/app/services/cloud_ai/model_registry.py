"""Model registry configuration for cloud AI providers."""

import sys
import os

# Add ai_council to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../.."))

from ai_council.core.models import TaskType
from typing import Dict, List, Any


# Model registry with all cloud models and their capabilities
MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "groq-llama3-70b": {
        "provider": "groq",
        "model_name": "llama3-70b-8192",
        "capabilities": [
            TaskType.REASONING,
            TaskType.RESEARCH,
            TaskType.CODE_GENERATION,
        ],
        "cost_per_input_token": 0.00000059,
        "cost_per_output_token": 0.00000079,
        "average_latency": 0.5,  # seconds
        "max_context": 8192,
        "reliability_score": 0.95,
    },
    "groq-mixtral-8x7b": {
        "provider": "groq",
        "model_name": "mixtral-8x7b-32768",
        "capabilities": [
            TaskType.REASONING,
            TaskType.CREATIVE_OUTPUT,
        ],
        "cost_per_input_token": 0.00000027,
        "cost_per_output_token": 0.00000027,
        "average_latency": 0.4,
        "max_context": 32768,
        "reliability_score": 0.93,
    },
    "together-mixtral-8x7b": {
        "provider": "together",
        "model_name": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "capabilities": [
            TaskType.REASONING,
            TaskType.CODE_GENERATION,
        ],
        "cost_per_input_token": 0.0000006,
        "cost_per_output_token": 0.0000006,
        "average_latency": 1.2,
        "max_context": 32768,
        "reliability_score": 0.92,
    },
    "together-llama2-70b": {
        "provider": "together",
        "model_name": "meta-llama/Llama-2-70b-chat-hf",
        "capabilities": [
            TaskType.RESEARCH,
            TaskType.CREATIVE_OUTPUT,
        ],
        "cost_per_input_token": 0.0000009,
        "cost_per_output_token": 0.0000009,
        "average_latency": 1.5,
        "max_context": 4096,
        "reliability_score": 0.90,
    },
    "openrouter-claude-3-sonnet": {
        "provider": "openrouter",
        "model_name": "anthropic/claude-3-sonnet",
        "capabilities": [
            TaskType.REASONING,
            TaskType.RESEARCH,
            TaskType.CODE_GENERATION,
            TaskType.FACT_CHECKING,
        ],
        "cost_per_input_token": 0.000003,
        "cost_per_output_token": 0.000015,
        "average_latency": 2.0,
        "max_context": 200000,
        "reliability_score": 0.98,
    },
    "openrouter-gpt4-turbo": {
        "provider": "openrouter",
        "model_name": "openai/gpt-4-turbo",
        "capabilities": [
            TaskType.REASONING,
            TaskType.CODE_GENERATION,
            TaskType.DEBUGGING,
        ],
        "cost_per_input_token": 0.00001,
        "cost_per_output_token": 0.00003,
        "average_latency": 3.0,
        "max_context": 128000,
        "reliability_score": 0.97,
    },
    "huggingface-mistral-7b": {
        "provider": "huggingface",
        "model_name": "mistralai/Mistral-7B-Instruct-v0.2",
        "capabilities": [
            TaskType.REASONING,
            TaskType.CREATIVE_OUTPUT,
        ],
        "cost_per_input_token": 0.0000002,
        "cost_per_output_token": 0.0000002,
        "average_latency": 2.5,
        "max_context": 32768,
        "reliability_score": 0.85,
    },
    # Ollama models (for local development/testing)
    "ollama-llama2": {
        "provider": "ollama",
        "model_name": "llama2",
        "capabilities": [
            TaskType.REASONING,
            TaskType.RESEARCH,
            TaskType.CREATIVE_OUTPUT,
        ],
        "cost_per_input_token": 0.0,  # Free for local
        "cost_per_output_token": 0.0,
        "average_latency": 3.0,  # Depends on hardware
        "max_context": 4096,
        "reliability_score": 0.85,
        "local_only": True,  # Indicates this is for local development
    },
    "ollama-mistral": {
        "provider": "ollama",
        "model_name": "mistral",
        "capabilities": [
            TaskType.REASONING,
            TaskType.CODE_GENERATION,
            TaskType.CREATIVE_OUTPUT,
        ],
        "cost_per_input_token": 0.0,
        "cost_per_output_token": 0.0,
        "average_latency": 2.5,
        "max_context": 8192,
        "reliability_score": 0.87,
        "local_only": True,
    },
    "ollama-codellama": {
        "provider": "ollama",
        "model_name": "codellama",
        "capabilities": [
            TaskType.CODE_GENERATION,
            TaskType.DEBUGGING,
        ],
        "cost_per_input_token": 0.0,
        "cost_per_output_token": 0.0,
        "average_latency": 3.5,
        "max_context": 4096,
        "reliability_score": 0.83,
        "local_only": True,
    },
}


def get_models_for_task_type(task_type: TaskType) -> List[str]:
    """Get list of model IDs that support a given task type.
    
    Args:
        task_type: The task type to filter by
        
    Returns:
        List of model IDs that support the task type
    """
    return [
        model_id
        for model_id, config in MODEL_REGISTRY.items()
        if task_type in config["capabilities"]
    ]


def get_model_config(model_id: str) -> Dict[str, Any]:
    """Get configuration for a specific model.
    
    Args:
        model_id: The model identifier
        
    Returns:
        Model configuration dictionary
        
    Raises:
        KeyError: If model_id is not found in registry
    """
    return MODEL_REGISTRY[model_id]


def get_cheapest_model_for_task(task_type: TaskType) -> str:
    """Get the cheapest model that supports a given task type.
    
    Args:
        task_type: The task type
        
    Returns:
        Model ID of the cheapest model
        
    Raises:
        ValueError: If no models support the task type
    """
    models = get_models_for_task_type(task_type)
    if not models:
        raise ValueError(f"No models found for task type: {task_type}")
    
    # Sort by average cost (input + output)
    cheapest = min(
        models,
        key=lambda m: (
            MODEL_REGISTRY[m]["cost_per_input_token"] +
            MODEL_REGISTRY[m]["cost_per_output_token"]
        )
    )
    return cheapest


def get_fastest_model_for_task(task_type: TaskType) -> str:
    """Get the fastest model that supports a given task type.
    
    Args:
        task_type: The task type
        
    Returns:
        Model ID of the fastest model
        
    Raises:
        ValueError: If no models support the task type
    """
    models = get_models_for_task_type(task_type)
    if not models:
        raise ValueError(f"No models found for task type: {task_type}")
    
    # Sort by average latency
    fastest = min(
        models,
        key=lambda m: MODEL_REGISTRY[m]["average_latency"]
    )
    return fastest


def get_best_quality_model_for_task(task_type: TaskType) -> str:
    """Get the highest quality model that supports a given task type.
    
    Args:
        task_type: The task type
        
    Returns:
        Model ID of the best quality model
        
    Raises:
        ValueError: If no models support the task type
    """
    models = get_models_for_task_type(task_type)
    if not models:
        raise ValueError(f"No models found for task type: {task_type}")
    
    # Sort by reliability score
    best = max(
        models,
        key=lambda m: MODEL_REGISTRY[m]["reliability_score"]
    )
    return best


def get_cloud_models_only() -> List[str]:
    """Get list of cloud-only model IDs (excludes local Ollama models).
    
    Returns:
        List of cloud model IDs
    """
    return [
        model_id
        for model_id, config in MODEL_REGISTRY.items()
        if not config.get("local_only", False)
    ]


def get_local_models_only() -> List[str]:
    """Get list of local Ollama model IDs.
    
    Returns:
        List of local model IDs
    """
    return [
        model_id
        for model_id, config in MODEL_REGISTRY.items()
        if config.get("local_only", False)
    ]


def is_local_model(model_id: str) -> bool:
    """Check if a model is a local Ollama model.
    
    Args:
        model_id: The model identifier
        
    Returns:
        True if model is local-only, False otherwise
    """
    if model_id not in MODEL_REGISTRY:
        return False
    return MODEL_REGISTRY[model_id].get("local_only", False)
