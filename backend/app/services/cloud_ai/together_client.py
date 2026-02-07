"""Together.ai API client."""

import httpx
from typing import Dict, Optional


class TogetherClient:
    """Client for Together.ai API."""
    
    BASE_URL = "https://api.together.xyz/v1"
    
    def __init__(self, api_key: str):
        """Initialize Together.ai client.
        
        Args:
            api_key: Together.ai API key for authentication
        """
        self.api_key = api_key
    
    def generate(self, prompt: str, model: str, **kwargs) -> str:
        """Generate response from Together.ai API.
        
        Args:
            prompt: The input prompt
            model: Model identifier (e.g., 'mistralai/Mixtral-8x7B-Instruct-v0.1', 'meta-llama/Llama-2-70b-chat-hf')
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
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "top_p": kwargs.get("top_p", 0.9),
            "top_k": kwargs.get("top_k", 50),
        }
        
        # Make synchronous request
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.BASE_URL}/inference",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            return data["output"]["choices"][0]["text"]
    
    async def generate_async(self, prompt: str, model: str, **kwargs) -> str:
        """Generate response from Together.ai API asynchronously.
        
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
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "top_p": kwargs.get("top_p", 0.9),
            "top_k": kwargs.get("top_k", 50),
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/inference",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            
            data = response.json()
            return data["output"]["choices"][0]["text"]
