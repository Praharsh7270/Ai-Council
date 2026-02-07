"""Ollama client for local development and testing."""

import httpx
from typing import Dict, Optional


class OllamaClient:
    """Client for Ollama local inference (for development/testing)."""
    
    def __init__(self, base_url: str = "http://localhost:11434", api_key: str = ""):
        """Initialize Ollama client.
        
        Args:
            base_url: Ollama server URL (default: http://localhost:11434)
            api_key: Not used for Ollama, kept for interface compatibility
        """
        self.base_url = base_url
    
    def generate(self, prompt: str, model: str, **kwargs) -> str:
        """Generate response from Ollama API.
        
        Args:
            prompt: The input prompt
            model: Model identifier (e.g., 'llama2', 'mistral', 'codellama')
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            str: The generated response text
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        # Prepare request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 1000),
            }
        }
        
        # Make synchronous request
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            return data["response"]
    
    async def generate_async(self, prompt: str, model: str, **kwargs) -> str:
        """Generate response from Ollama API asynchronously.
        
        Args:
            prompt: The input prompt
            model: Model identifier
            **kwargs: Additional parameters
            
        Returns:
            str: The generated response text
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 1000),
            }
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            
            data = response.json()
            return data["response"]
