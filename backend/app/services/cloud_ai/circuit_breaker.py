"""Circuit breaker implementation for cloud AI provider failures."""

import time
from typing import Dict, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failures detected, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Number of failures before opening
    timeout: float = 60.0  # Seconds to wait before trying again (half-open)
    success_threshold: int = 2  # Successes needed in half-open to close
    max_timeout: float = 300.0  # Maximum timeout (5 minutes)


@dataclass
class CircuitBreakerState:
    """State tracking for circuit breaker."""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    opened_at: Optional[float] = None
    timeout: float = 60.0  # Current timeout (increases with exponential backoff)


class CircuitBreaker:
    """Circuit breaker for handling provider failures with exponential backoff."""
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        """Initialize circuit breaker.
        
        Args:
            config: Circuit breaker configuration
        """
        self.config = config or CircuitBreakerConfig()
        self.states: Dict[str, CircuitBreakerState] = {}
    
    def get_state(self, provider: str) -> CircuitState:
        """Get current state for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            Current circuit state
        """
        if provider not in self.states:
            self.states[provider] = CircuitBreakerState()
        
        state = self.states[provider]
        
        # Check if we should transition from OPEN to HALF_OPEN
        if state.state == CircuitState.OPEN and state.opened_at:
            elapsed = time.time() - state.opened_at
            if elapsed >= state.timeout:
                state.state = CircuitState.HALF_OPEN
                state.success_count = 0
        
        return state.state
    
    def record_success(self, provider: str):
        """Record a successful request.
        
        Args:
            provider: Provider name
        """
        if provider not in self.states:
            self.states[provider] = CircuitBreakerState()
        
        state = self.states[provider]
        
        if state.state == CircuitState.HALF_OPEN:
            state.success_count += 1
            if state.success_count >= self.config.success_threshold:
                # Close the circuit - service recovered
                state.state = CircuitState.CLOSED
                state.failure_count = 0
                state.success_count = 0
                state.timeout = self.config.timeout  # Reset timeout
        elif state.state == CircuitState.CLOSED:
            # Reset failure count on success
            state.failure_count = 0
    
    def record_failure(self, provider: str):
        """Record a failed request.
        
        Args:
            provider: Provider name
        """
        if provider not in self.states:
            self.states[provider] = CircuitBreakerState()
        
        state = self.states[provider]
        state.failure_count += 1
        state.last_failure_time = time.time()
        
        if state.state == CircuitState.HALF_OPEN:
            # Failure in half-open state - reopen circuit
            state.state = CircuitState.OPEN
            state.opened_at = time.time()
            # Exponential backoff - double the timeout
            state.timeout = min(state.timeout * 2, self.config.max_timeout)
        elif state.state == CircuitState.CLOSED:
            # Check if we should open the circuit
            if state.failure_count >= self.config.failure_threshold:
                state.state = CircuitState.OPEN
                state.opened_at = time.time()
                state.timeout = self.config.timeout
    
    def is_available(self, provider: str) -> bool:
        """Check if provider is available (circuit not open).
        
        Args:
            provider: Provider name
            
        Returns:
            True if provider is available, False if circuit is open
        """
        current_state = self.get_state(provider)
        return current_state != CircuitState.OPEN
    
    def call(self, provider: str, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with circuit breaker protection.
        
        Args:
            provider: Provider name
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result of func execution
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Any exception raised by func
        """
        if not self.is_available(provider):
            raise CircuitBreakerOpenError(
                f"Circuit breaker is open for provider: {provider}"
            )
        
        try:
            result = func(*args, **kwargs)
            self.record_success(provider)
            return result
        except Exception as e:
            self.record_failure(provider)
            raise
    
    def get_fallback_provider(self, failed_provider: str, available_providers: list) -> Optional[str]:
        """Get a fallback provider when circuit is open.
        
        Args:
            failed_provider: The provider that failed
            available_providers: List of alternative providers
            
        Returns:
            Name of fallback provider, or None if none available
        """
        for provider in available_providers:
            if provider != failed_provider and self.is_available(provider):
                return provider
        return None
    
    def reset(self, provider: str):
        """Reset circuit breaker for a provider.
        
        Args:
            provider: Provider name
        """
        if provider in self.states:
            self.states[provider] = CircuitBreakerState()
    
    def get_stats(self, provider: str) -> Dict[str, Any]:
        """Get statistics for a provider's circuit breaker.
        
        Args:
            provider: Provider name
            
        Returns:
            Dictionary with circuit breaker statistics
        """
        if provider not in self.states:
            return {
                "state": "closed",
                "failure_count": 0,
                "success_count": 0,
                "timeout": self.config.timeout,
            }
        
        state = self.states[provider]
        return {
            "state": state.state.value,
            "failure_count": state.failure_count,
            "success_count": state.success_count,
            "timeout": state.timeout,
            "last_failure_time": state.last_failure_time,
            "opened_at": state.opened_at,
        }


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


# Global circuit breaker instance
_global_circuit_breaker: Optional[CircuitBreaker] = None


def get_circuit_breaker() -> CircuitBreaker:
    """Get the global circuit breaker instance.
    
    Returns:
        Global CircuitBreaker instance
    """
    global _global_circuit_breaker
    if _global_circuit_breaker is None:
        _global_circuit_breaker = CircuitBreaker()
    return _global_circuit_breaker
