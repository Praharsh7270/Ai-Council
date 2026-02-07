"""Property-based tests for circuit breaker functionality.

**Property 4: Circuit Breaker Activation on Failures**
**Validates: Requirements 1.4**
Test that 5+ failures open the circuit breaker
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import time

from app.services.cloud_ai.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerOpenError,
)


class TestCircuitBreaker:
    """Test circuit breaker behavior with failures and recovery."""
    
    @given(
        failure_count=st.integers(min_value=5, max_value=20),
        provider=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
    )
    @settings(max_examples=30, deadline=None)
    def test_circuit_opens_after_threshold_failures(self, failure_count, provider):
        """Property: Circuit breaker opens after reaching failure threshold.
        
        This test verifies that:
        1. Circuit starts in CLOSED state
        2. After 5 failures, circuit transitions to OPEN state
        3. Additional failures keep circuit OPEN
        """
        # Create circuit breaker with default config (threshold=5)
        cb = CircuitBreaker()
        
        # Initially circuit should be closed
        assert cb.get_state(provider) == CircuitState.CLOSED
        assert cb.is_available(provider) is True
        
        # Record failures
        for i in range(failure_count):
            cb.record_failure(provider)
            
            if i < 4:
                # Before threshold, should remain closed
                assert cb.get_state(provider) == CircuitState.CLOSED
            else:
                # At or after threshold, should be open
                assert cb.get_state(provider) == CircuitState.OPEN
                assert cb.is_available(provider) is False
    
    @given(
        failure_count=st.integers(min_value=1, max_value=4),
        provider=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
    )
    @settings(max_examples=20, deadline=None)
    def test_circuit_stays_closed_below_threshold(self, failure_count, provider):
        """Property: Circuit breaker stays closed below failure threshold.
        
        This test verifies that:
        1. Fewer than 5 failures keep circuit CLOSED
        2. Circuit remains available
        """
        cb = CircuitBreaker()
        
        # Record failures below threshold
        for _ in range(failure_count):
            cb.record_failure(provider)
        
        # Circuit should still be closed
        assert cb.get_state(provider) == CircuitState.CLOSED
        assert cb.is_available(provider) is True
    
    def test_circuit_transitions_to_half_open_after_timeout(self):
        """Test that circuit transitions from OPEN to HALF_OPEN after timeout."""
        # Create circuit breaker with short timeout
        config = CircuitBreakerConfig(failure_threshold=5, timeout=0.1)
        cb = CircuitBreaker(config)
        
        provider = "test_provider"
        
        # Trigger 5 failures to open circuit
        for _ in range(5):
            cb.record_failure(provider)
        
        assert cb.get_state(provider) == CircuitState.OPEN
        
        # Wait for timeout
        time.sleep(0.15)
        
        # Circuit should transition to HALF_OPEN
        assert cb.get_state(provider) == CircuitState.HALF_OPEN
    
    def test_circuit_closes_after_successes_in_half_open(self):
        """Test that circuit closes after successful requests in HALF_OPEN state."""
        config = CircuitBreakerConfig(
            failure_threshold=5,
            timeout=0.1,
            success_threshold=2
        )
        cb = CircuitBreaker(config)
        
        provider = "test_provider"
        
        # Open the circuit
        for _ in range(5):
            cb.record_failure(provider)
        
        assert cb.get_state(provider) == CircuitState.OPEN
        
        # Wait for timeout to transition to HALF_OPEN
        time.sleep(0.15)
        assert cb.get_state(provider) == CircuitState.HALF_OPEN
        
        # Record successes
        cb.record_success(provider)
        assert cb.get_state(provider) == CircuitState.HALF_OPEN
        
        cb.record_success(provider)
        # After 2 successes, should close
        assert cb.get_state(provider) == CircuitState.CLOSED
    
    def test_circuit_reopens_on_failure_in_half_open(self):
        """Test that circuit reopens if failure occurs in HALF_OPEN state."""
        config = CircuitBreakerConfig(failure_threshold=5, timeout=0.1)
        cb = CircuitBreaker(config)
        
        provider = "test_provider"
        
        # Open the circuit
        for _ in range(5):
            cb.record_failure(provider)
        
        # Wait for timeout
        time.sleep(0.15)
        assert cb.get_state(provider) == CircuitState.HALF_OPEN
        
        # Record a failure in HALF_OPEN
        cb.record_failure(provider)
        
        # Should reopen
        assert cb.get_state(provider) == CircuitState.OPEN
    
    def test_exponential_backoff_increases_timeout(self):
        """Test that timeout increases exponentially after repeated failures."""
        config = CircuitBreakerConfig(
            failure_threshold=5,
            timeout=1.0,
            max_timeout=10.0
        )
        cb = CircuitBreaker(config)
        
        provider = "test_provider"
        
        # First round of failures
        for _ in range(5):
            cb.record_failure(provider)
        
        stats = cb.get_stats(provider)
        initial_timeout = stats["timeout"]
        assert initial_timeout == 1.0
        
        # Transition to HALF_OPEN (simulate timeout)
        cb.states[provider].state = CircuitState.HALF_OPEN
        
        # Fail again to trigger exponential backoff
        cb.record_failure(provider)
        
        stats = cb.get_stats(provider)
        new_timeout = stats["timeout"]
        
        # Timeout should have doubled
        assert new_timeout == 2.0
        assert new_timeout > initial_timeout
    
    def test_success_resets_failure_count_in_closed_state(self):
        """Test that success resets failure count when circuit is closed."""
        cb = CircuitBreaker()
        provider = "test_provider"
        
        # Record some failures (below threshold)
        for _ in range(3):
            cb.record_failure(provider)
        
        stats = cb.get_stats(provider)
        assert stats["failure_count"] == 3
        
        # Record a success
        cb.record_success(provider)
        
        # Failure count should reset
        stats = cb.get_stats(provider)
        assert stats["failure_count"] == 0
    
    def test_fallback_provider_selection(self):
        """Test that fallback provider is selected when circuit is open."""
        cb = CircuitBreaker()
        
        provider1 = "provider1"
        provider2 = "provider2"
        provider3 = "provider3"
        
        # Open circuit for provider1
        for _ in range(5):
            cb.record_failure(provider1)
        
        # Get fallback
        fallback = cb.get_fallback_provider(
            provider1,
            [provider2, provider3]
        )
        
        # Should return an available provider
        assert fallback in [provider2, provider3]
        assert fallback != provider1
    
    def test_no_fallback_when_all_circuits_open(self):
        """Test that no fallback is returned when all circuits are open."""
        cb = CircuitBreaker()
        
        providers = ["provider1", "provider2", "provider3"]
        
        # Open all circuits
        for provider in providers:
            for _ in range(5):
                cb.record_failure(provider)
        
        # Try to get fallback
        fallback = cb.get_fallback_provider(
            "provider1",
            ["provider2", "provider3"]
        )
        
        # Should return None
        assert fallback is None
    
    def test_circuit_breaker_call_wrapper(self):
        """Test that circuit breaker call wrapper works correctly."""
        cb = CircuitBreaker()
        provider = "test_provider"
        
        # Define a function that succeeds
        def success_func():
            return "success"
        
        # Should work normally
        result = cb.call(provider, success_func)
        assert result == "success"
        
        # Open the circuit
        for _ in range(5):
            cb.record_failure(provider)
        
        # Should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(provider, success_func)
    
    def test_circuit_breaker_call_records_failures(self):
        """Test that circuit breaker call wrapper records failures."""
        cb = CircuitBreaker()
        provider = "test_provider"
        
        # Define a function that fails
        def fail_func():
            raise ValueError("Test error")
        
        # Call should raise the original exception
        for i in range(5):
            with pytest.raises(ValueError):
                cb.call(provider, fail_func)
        
        # Circuit should be open after 5 failures
        assert cb.get_state(provider) == CircuitState.OPEN
    
    @given(
        num_providers=st.integers(min_value=2, max_value=10),
    )
    @settings(max_examples=20, deadline=None)
    def test_independent_circuit_breakers_per_provider(self, num_providers):
        """Property: Each provider has independent circuit breaker state.
        
        This test verifies that:
        1. Failures in one provider don't affect others
        2. Each provider maintains separate state
        """
        cb = CircuitBreaker()
        
        # Create provider names
        providers = [f"provider_{i}" for i in range(num_providers)]
        
        # Open circuit for first provider only
        for _ in range(5):
            cb.record_failure(providers[0])
        
        # First provider should be open
        assert cb.get_state(providers[0]) == CircuitState.OPEN
        
        # All other providers should be closed
        for provider in providers[1:]:
            assert cb.get_state(provider) == CircuitState.CLOSED
            assert cb.is_available(provider) is True
