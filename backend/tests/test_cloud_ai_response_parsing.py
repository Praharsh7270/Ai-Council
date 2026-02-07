"""Property-based tests for cloud AI provider response parsing.

**Property 1: Cloud AI Provider Response Parsing**
**Validates: Requirements 1.3**
Test that valid responses from each provider parse to AgentResponse
"""

import pytest
from hypothesis import given, strategies as st, settings
import sys
import os

# Add ai_council to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from app.services.cloud_ai.adapter import CloudAIAdapter
from app.services.cloud_ai.groq_client import GroqClient
from app.services.cloud_ai.together_client import TogetherClient
from app.services.cloud_ai.openrouter_client import OpenRouterClient
from app.services.cloud_ai.huggingface_client import HuggingFaceClient


# Mock response data for each provider
MOCK_GROQ_RESPONSE = {
    "choices": [
        {
            "message": {
                "content": "This is a test response from Groq"
            }
        }
    ]
}

MOCK_TOGETHER_RESPONSE = {
    "output": {
        "choices": [
            {
                "text": "This is a test response from Together.ai"
            }
        ]
    }
}

MOCK_OPENROUTER_RESPONSE = {
    "choices": [
        {
            "message": {
                "content": "This is a test response from OpenRouter"
            }
        }
    ]
}

MOCK_HUGGINGFACE_RESPONSE = [
    {
        "generated_text": "This is a test response from HuggingFace"
    }
]


class TestCloudAIResponseParsing:
    """Test that cloud AI provider responses parse correctly."""
    
    @given(
        provider=st.sampled_from(['groq', 'together', 'openrouter', 'huggingface']),
        prompt=st.text(min_size=1, max_size=100),
    )
    @settings(max_examples=20, deadline=None)
    def test_provider_response_parsing(self, provider, prompt):
        """Property: Valid responses from each provider parse to string output.
        
        This test verifies that:
        1. Each provider client can parse its response format
        2. The parsed response is a non-empty string
        3. The CloudAIAdapter correctly delegates to the provider client
        """
        import httpx
        from unittest.mock import Mock, patch
        
        # Mock the HTTP requests for each provider
        def mock_groq_post(*args, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.json = Mock(return_value=MOCK_GROQ_RESPONSE)
            return mock_response
        
        def mock_together_post(*args, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.json = Mock(return_value=MOCK_TOGETHER_RESPONSE)
            return mock_response
        
        def mock_openrouter_post(*args, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.json = Mock(return_value=MOCK_OPENROUTER_RESPONSE)
            return mock_response
        
        def mock_huggingface_post(*args, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.json = Mock(return_value=MOCK_HUGGINGFACE_RESPONSE)
            return mock_response
        
        # Select appropriate mock and model based on provider
        if provider == 'groq':
            mock_post = mock_groq_post
            model_name = "llama3-70b-8192"
        elif provider == 'together':
            mock_post = mock_together_post
            model_name = "mistralai/Mixtral-8x7B-Instruct-v0.1"
        elif provider == 'openrouter':
            mock_post = mock_openrouter_post
            model_name = "anthropic/claude-3-sonnet"
        else:  # huggingface
            mock_post = mock_huggingface_post
            model_name = "mistralai/Mistral-7B-Instruct-v0.2"
        
        # Patch httpx.Client.post for this test
        with patch.object(httpx.Client, 'post', mock_post):
            # Create adapter and test response parsing
            adapter = CloudAIAdapter(
                provider=provider,
                model_id=model_name,
                api_key="test_key"
            )
            
            # Generate response
            response = adapter.generate_response(prompt)
            
            # Verify response is a non-empty string
            assert isinstance(response, str), f"Response should be string, got {type(response)}"
            assert len(response) > 0, "Response should not be empty"
            
            # Verify model_id format
            model_id = adapter.get_model_id()
            assert model_id.startswith(provider), f"Model ID should start with provider name"
            assert "-" in model_id, "Model ID should contain separator"
    
    def test_groq_response_structure(self):
        """Test that Groq client correctly parses response structure."""
        import httpx
        
        def mock_post(*args, **kwargs):
            class MockResponse:
                def raise_for_status(self):
                    pass
                def json(self):
                    return MOCK_GROQ_RESPONSE
            return MockResponse()
        
        # Monkey patch for this test
        original_client = httpx.Client
        
        class MockClient:
            def __init__(self, *args, **kwargs):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def post(self, *args, **kwargs):
                return mock_post()
        
        httpx.Client = MockClient
        
        try:
            client = GroqClient(api_key="test_key")
            response = client.generate("test prompt", "llama3-70b-8192")
            assert response == "This is a test response from Groq"
        finally:
            httpx.Client = original_client
    
    def test_together_response_structure(self):
        """Test that Together.ai client correctly parses response structure."""
        import httpx
        
        def mock_post(*args, **kwargs):
            class MockResponse:
                def raise_for_status(self):
                    pass
                def json(self):
                    return MOCK_TOGETHER_RESPONSE
            return MockResponse()
        
        original_client = httpx.Client
        
        class MockClient:
            def __init__(self, *args, **kwargs):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def post(self, *args, **kwargs):
                return mock_post()
        
        httpx.Client = MockClient
        
        try:
            client = TogetherClient(api_key="test_key")
            response = client.generate("test prompt", "mistralai/Mixtral-8x7B-Instruct-v0.1")
            assert response == "This is a test response from Together.ai"
        finally:
            httpx.Client = original_client
    
    def test_openrouter_response_structure(self):
        """Test that OpenRouter client correctly parses response structure."""
        import httpx
        
        def mock_post(*args, **kwargs):
            class MockResponse:
                def raise_for_status(self):
                    pass
                def json(self):
                    return MOCK_OPENROUTER_RESPONSE
            return MockResponse()
        
        original_client = httpx.Client
        
        class MockClient:
            def __init__(self, *args, **kwargs):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def post(self, *args, **kwargs):
                return mock_post()
        
        httpx.Client = MockClient
        
        try:
            client = OpenRouterClient(api_key="test_key")
            response = client.generate("test prompt", "anthropic/claude-3-sonnet")
            assert response == "This is a test response from OpenRouter"
        finally:
            httpx.Client = original_client
    
    def test_huggingface_response_structure(self):
        """Test that HuggingFace client correctly parses response structure."""
        import httpx
        
        def mock_post(*args, **kwargs):
            class MockResponse:
                def raise_for_status(self):
                    pass
                def json(self):
                    return MOCK_HUGGINGFACE_RESPONSE
            return MockResponse()
        
        original_client = httpx.Client
        
        class MockClient:
            def __init__(self, *args, **kwargs):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def post(self, *args, **kwargs):
                return mock_post()
        
        httpx.Client = MockClient
        
        try:
            client = HuggingFaceClient(api_key="test_key")
            response = client.generate("test prompt", "mistralai/Mistral-7B-Instruct-v0.2")
            assert response == "This is a test response from HuggingFace"
        finally:
            httpx.Client = original_client
