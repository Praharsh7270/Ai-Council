"""Configuration for AI provider selection (cloud vs local)."""

import os
from typing import List, Optional
from enum import Enum


class DeploymentMode(Enum):
    """Deployment mode for AI providers."""
    CLOUD = "cloud"  # Use cloud AI providers (production)
    LOCAL = "local"  # Use Ollama for local development
    HYBRID = "hybrid"  # Use both cloud and local


def get_deployment_mode() -> DeploymentMode:
    """Get the current deployment mode from environment.
    
    Returns:
        DeploymentMode enum value
    """
    mode = os.getenv("AI_DEPLOYMENT_MODE", "cloud").lower()
    
    if mode == "local":
        return DeploymentMode.LOCAL
    elif mode == "hybrid":
        return DeploymentMode.HYBRID
    else:
        return DeploymentMode.CLOUD


def should_use_cloud_providers() -> bool:
    """Check if cloud providers should be used.
    
    Returns:
        True if cloud providers should be used
    """
    mode = get_deployment_mode()
    return mode in [DeploymentMode.CLOUD, DeploymentMode.HYBRID]


def should_use_local_providers() -> bool:
    """Check if local Ollama providers should be used.
    
    Returns:
        True if local providers should be used
    """
    mode = get_deployment_mode()
    return mode in [DeploymentMode.LOCAL, DeploymentMode.HYBRID]


def get_ollama_base_url() -> str:
    """Get Ollama base URL from environment.
    
    Returns:
        Ollama base URL
    """
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def is_ollama_available() -> bool:
    """Check if Ollama is available locally.
    
    Returns:
        True if Ollama is running and accessible
    """
    import httpx
    
    try:
        base_url = get_ollama_base_url()
        with httpx.Client(timeout=2.0) as client:
            response = client.get(f"{base_url}/api/tags")
            return response.status_code == 200
    except Exception:
        return False


def get_available_providers() -> List[str]:
    """Get list of available providers based on configuration.
    
    Returns:
        List of provider names that are available
    """
    providers = []
    
    if should_use_cloud_providers():
        # Add cloud providers if API keys are configured
        if os.getenv("GROQ_API_KEY"):
            providers.append("groq")
        if os.getenv("TOGETHER_API_KEY"):
            providers.append("together")
        if os.getenv("OPENROUTER_API_KEY"):
            providers.append("openrouter")
        if os.getenv("HUGGINGFACE_API_KEY"):
            providers.append("huggingface")
    
    if should_use_local_providers() and is_ollama_available():
        providers.append("ollama")
    
    return providers


def get_provider_priority() -> List[str]:
    """Get provider priority order based on deployment mode.
    
    For CLOUD mode: prioritize cloud providers
    For LOCAL mode: use only Ollama
    For HYBRID mode: prefer cloud but fallback to local
    
    Returns:
        List of providers in priority order
    """
    mode = get_deployment_mode()
    
    if mode == DeploymentMode.LOCAL:
        return ["ollama"]
    elif mode == DeploymentMode.CLOUD:
        return ["groq", "together", "openrouter", "huggingface"]
    else:  # HYBRID
        return ["groq", "together", "openrouter", "huggingface", "ollama"]
