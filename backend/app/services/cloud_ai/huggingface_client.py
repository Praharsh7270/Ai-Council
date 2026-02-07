"""HuggingFace Inference API client."""

import httpx
from typing import Dict, Optional


class HuggingFaceClient:
    """Client for HuggingFace Inference API."""
    
    BASE_URL = "https://api-inference.huggingface.co/models"
    
    def __init__(self, api_key: str):
        """Initialize HuggingFace client.
        
        Args:
            api_key: HuggingFace API key for authentication
        """
        self.api_key = api_key
    
    def generate(self, prompt: str, model: str, **kwargs) -> str:
        """Generate response from HuggingFace Inference API.
        
        Args:
            prompt: The input prompt
            model: Model identifier (e.g., 'mistralai/Mistral-7B-Instruct-v0.2')
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            str: The generated response text
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        # Prepare request payload
        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": kwargs.get("temperature", 0.7),
                "max_new_tokens": kwargs.get("max_tokens", 1000),
                "top_p": kwargs.get("top_p", 0.9),
                "do_sample": True,
            }
        }
        
        # Make synchronous request
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.BASE_URL}/{model}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            # HuggingFace returns array of results
            if isinstance(data, list) and len(data) > 0:
                return data[0]["generated_text"]
            else:
                raise ValueError(f"Unexpected response format: {data}")
    
    async def generate_async(self, prompt: str, model: str, **kwargs) -> str:
        """Generate response from HuggingFace Inference API asynchronously.
        
        Args:
            prompt: The input prompt
            model: Model identifier
            **kwargs: Additional parameters
            
        Returns:
            str: The generated response text
        """
        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": kwargs.get("temperature", 0.7),
                "max_new_tokens": kwargs.get("max_tokens", 1000),
                "top_p": kwargs.get("top_p", 0.9),
                "do_sample": True,
            }
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/{model}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0]["generated_text"]
            else:
                raise ValueError(f"Unexpected response format: {data}")
