"""Provider health check service for monitoring cloud AI providers."""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import httpx

from app.core.redis import redis_client
from app.services.cloud_ai.circuit_breaker import get_circuit_breaker

logger = logging.getLogger(__name__)


class ProviderHealthStatus:
    """Health status for a cloud AI provider."""
    
    def __init__(
        self,
        status: str,
        last_check: datetime,
        response_time_ms: Optional[float] = None,
        error_message: Optional[str] = None
    ):
        self.status = status  # "healthy", "degraded", or "down"
        self.last_check = last_check
        self.response_time_ms = response_time_ms
        self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "status": self.status,
            "last_check": self.last_check.isoformat(),
            "response_time_ms": self.response_time_ms,
            "error_message": self.error_message
        }


class ProviderHealthChecker:
    """Health checker for cloud AI providers with caching."""
    
    # Provider health check endpoints (lightweight endpoints for health checks)
    HEALTH_CHECK_ENDPOINTS = {
        "groq": "https://api.groq.com/openai/v1/models",
        "together": "https://api.together.xyz/v1/models",
        "openrouter": "https://openrouter.ai/api/v1/models",
        "huggingface": "https://huggingface.co/api/models"
    }
    
    CACHE_TTL = 60  # Cache health status for 1 minute
    TIMEOUT = 5.0  # 5 second timeout for health checks
    
    def __init__(self):
        self.circuit_breaker = get_circuit_breaker()
    
    def _get_cache_key(self, provider: str) -> str:
        """Get Redis cache key for provider health status."""
        return f"provider:health:{provider}"
    
    async def _check_provider_endpoint(self, provider: str, url: str) -> ProviderHealthStatus:
        """
        Check a single provider's health by pinging its endpoint.
        
        Args:
            provider: Provider name
            url: Health check endpoint URL
            
        Returns:
            ProviderHealthStatus object
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(url)
                
                response_time_ms = (time.time() - start_time) * 1000
                
                # Check response status
                if response.status_code == 200:
                    # Healthy response
                    status = "healthy"
                    error_message = None
                elif 200 < response.status_code < 500:
                    # Degraded (client error but server is responding)
                    status = "degraded"
                    error_message = f"HTTP {response.status_code}"
                else:
                    # Down (server error)
                    status = "down"
                    error_message = f"HTTP {response.status_code}"
                
                return ProviderHealthStatus(
                    status=status,
                    last_check=datetime.utcnow(),
                    response_time_ms=response_time_ms,
                    error_message=error_message
                )
                
        except httpx.TimeoutException:
            response_time_ms = (time.time() - start_time) * 1000
            return ProviderHealthStatus(
                status="down",
                last_check=datetime.utcnow(),
                response_time_ms=response_time_ms,
                error_message="Request timeout"
            )
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Error checking health for {provider}: {e}")
            return ProviderHealthStatus(
                status="down",
                last_check=datetime.utcnow(),
                response_time_ms=response_time_ms,
                error_message=str(e)
            )
    
    async def check_provider_health(self, provider: str) -> ProviderHealthStatus:
        """
        Check health of a single provider with caching.
        
        Args:
            provider: Provider name
            
        Returns:
            ProviderHealthStatus object
        """
        # Try to get from cache first
        try:
            cache_key = self._get_cache_key(provider)
            cached_data = await redis_client.client.get(cache_key)
            
            if cached_data:
                # Parse cached data
                import json
                data = json.loads(cached_data)
                return ProviderHealthStatus(
                    status=data["status"],
                    last_check=datetime.fromisoformat(data["last_check"]),
                    response_time_ms=data.get("response_time_ms"),
                    error_message=data.get("error_message")
                )
        except Exception as e:
            logger.warning(f"Error reading health cache for {provider}: {e}")
        
        # Cache miss or error - perform health check
        if provider not in self.HEALTH_CHECK_ENDPOINTS:
            return ProviderHealthStatus(
                status="down",
                last_check=datetime.utcnow(),
                error_message=f"Unknown provider: {provider}"
            )
        
        url = self.HEALTH_CHECK_ENDPOINTS[provider]
        health_status = await self._check_provider_endpoint(provider, url)
        
        # Also consider circuit breaker state
        circuit_state = self.circuit_breaker.get_state(provider)
        if circuit_state.value == "open":
            # Circuit breaker is open - provider is down
            health_status.status = "down"
            if not health_status.error_message:
                health_status.error_message = "Circuit breaker open"
        elif circuit_state.value == "half_open":
            # Circuit breaker is testing - provider is degraded
            if health_status.status == "healthy":
                health_status.status = "degraded"
        
        # Cache the result
        try:
            cache_key = self._get_cache_key(provider)
            import json
            cache_data = json.dumps(health_status.to_dict())
            await redis_client.client.setex(
                cache_key,
                self.CACHE_TTL,
                cache_data
            )
        except Exception as e:
            logger.warning(f"Error caching health status for {provider}: {e}")
        
        return health_status
    
    async def check_all_providers(self) -> Dict[str, ProviderHealthStatus]:
        """
        Check health of all providers concurrently.
        
        Returns:
            Dictionary mapping provider names to health status
        """
        providers = list(self.HEALTH_CHECK_ENDPOINTS.keys())
        
        # Check all providers concurrently
        tasks = [
            self.check_provider_health(provider)
            for provider in providers
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build result dictionary
        health_statuses = {}
        for provider, result in zip(providers, results):
            if isinstance(result, Exception):
                logger.error(f"Error checking health for {provider}: {result}")
                health_statuses[provider] = ProviderHealthStatus(
                    status="down",
                    last_check=datetime.utcnow(),
                    error_message=str(result)
                )
            else:
                health_statuses[provider] = result
        
        return health_statuses


# Global health checker instance
_health_checker: Optional[ProviderHealthChecker] = None


def get_health_checker() -> ProviderHealthChecker:
    """Get the global health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = ProviderHealthChecker()
    return _health_checker
