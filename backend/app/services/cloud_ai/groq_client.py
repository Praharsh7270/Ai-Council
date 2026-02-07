"""Groq API client for ultra-fast inference."""

import httpx
from typing import Dict, List, Optional


class GroqClient:
    """Client for Groq API (ultra-fast inference)."""
    
    BASE_URL = "https://api.groq.com/openai/v1"
    
    def __init__(self, api_key: str):
        """Initialize Groq client.
        
        Args:
            api_key: Groq API key for authentication
        """
        self.api_key = api_key
    
    def generate(self, prompt: str, model: str, **kwargs) -> str:
        """Generate response from Groq API.
        
        Args:
            prompt: The input prompt
            model: Model identifier (e.g., 'llama3-70b-8192', 'mixtral-8x7b-32768')
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            str: The generated response text
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        # Prepare messages in chat format
        messages = [{"role": "user", "content": prompt}]
        
        # Prepare request payload
        payload = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
        }
        
        # Make synchronous request
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def generate_async(self, prompt: str, model: str, **kwargs) -> str:
        """Generate response from Groq API asynchronously.
        
        Args:
            prompt: The input prompt
            model: Model identifier
            **kwargs: Additional parameters
            
        Returns:
            str: The generated response text
        """
        messages = [{"role": "user", "content": prompt}]
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
