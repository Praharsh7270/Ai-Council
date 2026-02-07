"""Cloud AI Provider Adapter implementing AIModel interface."""

from abc import ABC
from typing import Optional
import sys
import os

# Add ai_council to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../.."))

from ai_council.core.interfaces import AIModel
from .circuit_breaker import get_circuit_breaker, CircuitBreakerOpenError


class CloudAIAdapter(AIModel):
    """Adapter for cloud AI providers that implements AIModel interface from AI Council."""
    
    def __init__(self, provider: str, model_id: str, api_key: str):
        """Initialize the cloud AI adapter.
        
        Args:
            provider: Provider name ('groq', 'together', 'openrouter', 'huggingface')
            model_id: Model identifier for the provider
            api_key: API key for authentication
        """
        self.provider = provider
        self.model_id = model_id
        self.api_key = api_key
        self.client = self._create_client()
        self.circuit_breaker = get_circuit_breaker()
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response from cloud AI provider with circuit breaker protection.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional model-specific parameters
            
        Returns:
            str: The generated response
            
        Raises:
            CircuitBreakerOpenError: If circuit breaker is open for this provider
        """
        # Check if circuit breaker allows the request
        if not self.circuit_breaker.is_available(self.provider):
            raise CircuitBreakerOpenError(
                f"Circuit breaker is open for provider: {self.provider}"
            )
        
        try:
            # Delegate to provider-specific client
            response = self.client.generate(prompt, self.model_id, **kwargs)
            # Record success
            self.circuit_breaker.record_success(self.provider)
            return response
        except Exception as e:
            # Record failure
            self.circuit_breaker.record_failure(self.provider)
            raise
    
    def get_model_id(self) -> str:
        """Get the unique identifier for this model.
        
        Returns:
            str: Model identifier in format 'provider-model_id'
        """
        return f"{self.provider}-{self.model_id}"
    
    def _create_client(self):
        """Create provider-specific HTTP client.
        
        Returns:
            Provider-specific client instance
            
        Raises:
            ValueError: If provider is not supported
        """
        from .groq_client import GroqClient
        from .together_client import TogetherClient
        from .openrouter_client import OpenRouterClient
        from .huggingface_client import HuggingFaceClient
        from .ollama_client import OllamaClient
        
        if self.provider == 'groq':
            return GroqClient(api_key=self.api_key)
        elif self.provider == 'together':
            return TogetherClient(api_key=self.api_key)
        elif self.provider == 'openrouter':
            return OpenRouterClient(api_key=self.api_key)
        elif self.provider == 'huggingface':
            return HuggingFaceClient(api_key=self.api_key)
        elif self.provider == 'ollama':
            # For local development/testing
            return OllamaClient(api_key=self.api_key)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
