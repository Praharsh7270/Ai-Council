"""Verification script for cloud AI integration.

This script verifies:
1. All cloud provider clients work with test API keys
2. Model registry is correctly configured
3. Circuit breaker functionality works as expected

Run this script to checkpoint the cloud AI integration before proceeding.
"""

import os
import sys
from typing import Dict, List, Tuple
from enum import Enum

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.cloud_ai.adapter import CloudAIAdapter
from app.services.cloud_ai.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
)
from app.services.cloud_ai.model_registry import (
    MODEL_REGISTRY,
    get_models_for_task_type,
    get_cheapest_model_for_task,
    get_fastest_model_for_task,
    get_best_quality_model_for_task,
    get_cloud_models_only,
)
from app.services.cloud_ai.config import (
    get_deployment_mode,
    get_available_providers,
    should_use_cloud_providers,
)
from ai_council.core.models import TaskType


class TestResult(Enum):
    """Test result status."""
    PASS = "✓ PASS"
    FAIL = "✗ FAIL"
    SKIP = "⊘ SKIP"
    WARN = "⚠ WARN"


class VerificationReport:
    """Collects and displays verification results."""
    
    def __init__(self):
        self.results: List[Tuple[str, TestResult, str]] = []
        self.warnings: List[str] = []
        self.errors: List[str] = []
    
    def add_result(self, test_name: str, result: TestResult, details: str = ""):
        """Add a test result."""
        self.results.append((test_name, result, details))
        
        if result == TestResult.FAIL:
            self.errors.append(f"{test_name}: {details}")
        elif result == TestResult.WARN:
            self.warnings.append(f"{test_name}: {details}")
    
    def print_summary(self):
        """Print verification summary."""
        print("\n" + "=" * 80)
        print("CLOUD AI INTEGRATION VERIFICATION REPORT")
        print("=" * 80 + "\n")
        
        # Print all results
        for test_name, result, details in self.results:
            status = result.value
            print(f"{status} {test_name}")
            if details:
                print(f"    {details}")
        
        # Print summary counts
        print("\n" + "-" * 80)
        passed = sum(1 for _, r, _ in self.results if r == TestResult.PASS)
        failed = sum(1 for _, r, _ in self.results if r == TestResult.FAIL)
        skipped = sum(1 for _, r, _ in self.results if r == TestResult.SKIP)
        warned = sum(1 for _, r, _ in self.results if r == TestResult.WARN)
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")
        print(f"Warnings: {warned}")
        
        # Print warnings
        if self.warnings:
            print("\n" + "-" * 80)
            print("WARNINGS:")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")
        
        # Print errors
        if self.errors:
            print("\n" + "-" * 80)
            print("ERRORS:")
            for error in self.errors:
                print(f"  ✗ {error}")
        
        # Overall status
        print("\n" + "=" * 80)
        if failed == 0:
            print("✓ VERIFICATION PASSED - Cloud AI integration is ready!")
        else:
            print("✗ VERIFICATION FAILED - Please fix the errors above")
        print("=" * 80 + "\n")
        
        return failed == 0


def verify_environment_variables(report: VerificationReport):
    """Verify that required environment variables are set."""
    print("\n[1/4] Verifying Environment Variables...")
    
    # Check deployment mode
    mode = get_deployment_mode()
    report.add_result(
        "Deployment Mode",
        TestResult.PASS,
        f"Mode: {mode.value}"
    )
    
    # Check if cloud providers should be used
    if should_use_cloud_providers():
        # Check API keys for cloud providers
        providers = {
            "GROQ_API_KEY": "Groq",
            "TOGETHER_API_KEY": "Together.ai",
            "OPENROUTER_API_KEY": "OpenRouter",
            "HUGGINGFACE_API_KEY": "HuggingFace",
        }
        
        for env_var, provider_name in providers.items():
            api_key = os.getenv(env_var)
            if api_key and api_key != f"your-{env_var.lower().replace('_', '-')}":
                report.add_result(
                    f"{provider_name} API Key",
                    TestResult.PASS,
                    f"Key configured (length: {len(api_key)})"
                )
            else:
                report.add_result(
                    f"{provider_name} API Key",
                    TestResult.WARN,
                    "Not configured or using placeholder value"
                )
    else:
        report.add_result(
            "Cloud Provider API Keys",
            TestResult.SKIP,
            "Cloud providers not enabled in deployment mode"
        )


def verify_model_registry(report: VerificationReport):
    """Verify that model registry is correctly configured."""
    print("\n[2/4] Verifying Model Registry Configuration...")
    
    # Check that registry is not empty
    if not MODEL_REGISTRY:
        report.add_result(
            "Model Registry",
            TestResult.FAIL,
            "Model registry is empty"
        )
        return
    
    report.add_result(
        "Model Registry",
        TestResult.PASS,
        f"Contains {len(MODEL_REGISTRY)} models"
    )
    
    # Verify all models have required fields
    required_fields = [
        "provider",
        "model_name",
        "capabilities",
        "cost_per_input_token",
        "cost_per_output_token",
        "average_latency",
        "max_context",
        "reliability_score",
    ]
    
    all_valid = True
    for model_id, config in MODEL_REGISTRY.items():
        missing_fields = [f for f in required_fields if f not in config]
        if missing_fields:
            report.add_result(
                f"Model {model_id}",
                TestResult.FAIL,
                f"Missing fields: {', '.join(missing_fields)}"
            )
            all_valid = False
    
    if all_valid:
        report.add_result(
            "Model Configuration Fields",
            TestResult.PASS,
            "All models have required fields"
        )
    
    # Verify coverage for important task types
    important_tasks = [
        TaskType.REASONING,
        TaskType.RESEARCH,
        TaskType.CODE_GENERATION,
        TaskType.CREATIVE_OUTPUT,
    ]
    
    for task_type in important_tasks:
        models = get_models_for_task_type(task_type)
        if models:
            report.add_result(
                f"Task Coverage: {task_type.value}",
                TestResult.PASS,
                f"{len(models)} models available"
            )
        else:
            report.add_result(
                f"Task Coverage: {task_type.value}",
                TestResult.WARN,
                "No models available for this task type"
            )
    
    # Verify routing functions work
    try:
        cheapest = get_cheapest_model_for_task(TaskType.REASONING)
        report.add_result(
            "Cheapest Model Selection",
            TestResult.PASS,
            f"Selected: {cheapest}"
        )
    except Exception as e:
        report.add_result(
            "Cheapest Model Selection",
            TestResult.FAIL,
            str(e)
        )
    
    try:
        fastest = get_fastest_model_for_task(TaskType.REASONING)
        report.add_result(
            "Fastest Model Selection",
            TestResult.PASS,
            f"Selected: {fastest}"
        )
    except Exception as e:
        report.add_result(
            "Fastest Model Selection",
            TestResult.FAIL,
            str(e)
        )
    
    try:
        best = get_best_quality_model_for_task(TaskType.REASONING)
        report.add_result(
            "Best Quality Model Selection",
            TestResult.PASS,
            f"Selected: {best}"
        )
    except Exception as e:
        report.add_result(
            "Best Quality Model Selection",
            TestResult.FAIL,
            str(e)
        )
    
    # Verify cloud models are available
    cloud_models = get_cloud_models_only()
    if cloud_models:
        report.add_result(
            "Cloud Models",
            TestResult.PASS,
            f"{len(cloud_models)} cloud models configured"
        )
    else:
        report.add_result(
            "Cloud Models",
            TestResult.WARN,
            "No cloud models configured"
        )


def verify_circuit_breaker(report: VerificationReport):
    """Verify that circuit breaker functionality works."""
    print("\n[3/4] Verifying Circuit Breaker Functionality...")
    
    # Test basic circuit breaker creation
    try:
        cb = CircuitBreaker()
        report.add_result(
            "Circuit Breaker Creation",
            TestResult.PASS,
            "Circuit breaker initialized successfully"
        )
    except Exception as e:
        report.add_result(
            "Circuit Breaker Creation",
            TestResult.FAIL,
            str(e)
        )
        return
    
    # Test initial state
    test_provider = "test_provider"
    initial_state = cb.get_state(test_provider)
    if initial_state == CircuitState.CLOSED:
        report.add_result(
            "Initial Circuit State",
            TestResult.PASS,
            "Circuit starts in CLOSED state"
        )
    else:
        report.add_result(
            "Initial Circuit State",
            TestResult.FAIL,
            f"Expected CLOSED, got {initial_state}"
        )
    
    # Test failure threshold
    for i in range(5):
        cb.record_failure(test_provider)
    
    state_after_failures = cb.get_state(test_provider)
    if state_after_failures == CircuitState.OPEN:
        report.add_result(
            "Circuit Opens After Failures",
            TestResult.PASS,
            "Circuit opened after 5 failures"
        )
    else:
        report.add_result(
            "Circuit Opens After Failures",
            TestResult.FAIL,
            f"Expected OPEN, got {state_after_failures}"
        )
    
    # Test availability check
    is_available = cb.is_available(test_provider)
    if not is_available:
        report.add_result(
            "Circuit Availability Check",
            TestResult.PASS,
            "Open circuit correctly reports unavailable"
        )
    else:
        report.add_result(
            "Circuit Availability Check",
            TestResult.FAIL,
            "Open circuit should not be available"
        )
    
    # Test fallback provider selection
    fallback = cb.get_fallback_provider(test_provider, ["provider2", "provider3"])
    if fallback in ["provider2", "provider3"]:
        report.add_result(
            "Fallback Provider Selection",
            TestResult.PASS,
            f"Selected fallback: {fallback}"
        )
    else:
        report.add_result(
            "Fallback Provider Selection",
            TestResult.FAIL,
            f"Invalid fallback: {fallback}"
        )
    
    # Test circuit breaker stats
    try:
        stats = cb.get_stats(test_provider)
        if "state" in stats and "failure_count" in stats:
            report.add_result(
                "Circuit Breaker Statistics",
                TestResult.PASS,
                f"State: {stats['state']}, Failures: {stats['failure_count']}"
            )
        else:
            report.add_result(
                "Circuit Breaker Statistics",
                TestResult.FAIL,
                "Missing required fields in stats"
            )
    except Exception as e:
        report.add_result(
            "Circuit Breaker Statistics",
            TestResult.FAIL,
            str(e)
        )
    
    # Test reset functionality
    try:
        cb.reset(test_provider)
        reset_state = cb.get_state(test_provider)
        if reset_state == CircuitState.CLOSED:
            report.add_result(
                "Circuit Breaker Reset",
                TestResult.PASS,
                "Circuit reset to CLOSED state"
            )
        else:
            report.add_result(
                "Circuit Breaker Reset",
                TestResult.FAIL,
                f"Expected CLOSED after reset, got {reset_state}"
            )
    except Exception as e:
        report.add_result(
            "Circuit Breaker Reset",
            TestResult.FAIL,
            str(e)
        )


def verify_provider_clients(report: VerificationReport):
    """Verify that provider clients can be instantiated."""
    print("\n[4/4] Verifying Provider Client Instantiation...")
    
    # Test each provider client
    providers = [
        ("groq", "llama3-70b-8192", "GROQ_API_KEY"),
        ("together", "mistralai/Mixtral-8x7B-Instruct-v0.1", "TOGETHER_API_KEY"),
        ("openrouter", "anthropic/claude-3-sonnet", "OPENROUTER_API_KEY"),
        ("huggingface", "mistralai/Mistral-7B-Instruct-v0.2", "HUGGINGFACE_API_KEY"),
    ]
    
    for provider, model_id, env_var in providers:
        api_key = os.getenv(env_var, "test_key")
        
        try:
            # Try to create adapter
            adapter = CloudAIAdapter(
                provider=provider,
                model_id=model_id,
                api_key=api_key
            )
            
            # Verify adapter properties
            adapter_model_id = adapter.get_model_id()
            expected_format = f"{provider}-{model_id}"
            
            if adapter_model_id == expected_format:
                report.add_result(
                    f"{provider.capitalize()} Client",
                    TestResult.PASS,
                    f"Adapter created successfully (model_id: {adapter_model_id})"
                )
            else:
                report.add_result(
                    f"{provider.capitalize()} Client",
                    TestResult.WARN,
                    f"Model ID format unexpected: {adapter_model_id}"
                )
        except Exception as e:
            report.add_result(
                f"{provider.capitalize()} Client",
                TestResult.FAIL,
                f"Failed to create adapter: {str(e)}"
            )
    
    # Note about actual API calls
    report.add_result(
        "Live API Testing",
        TestResult.SKIP,
        "Live API calls not tested (requires valid API keys and credits)"
    )


def main():
    """Run all verification checks."""
    print("\n" + "=" * 80)
    print("CLOUD AI INTEGRATION VERIFICATION")
    print("=" * 80)
    print("\nThis script verifies:")
    print("  1. Environment variables are configured")
    print("  2. Model registry is correctly set up")
    print("  3. Circuit breaker functionality works")
    print("  4. Provider clients can be instantiated")
    print("\nNote: This does NOT make live API calls to avoid using credits.")
    print("=" * 80)
    
    report = VerificationReport()
    
    try:
        verify_environment_variables(report)
        verify_model_registry(report)
        verify_circuit_breaker(report)
        verify_provider_clients(report)
    except Exception as e:
        print(f"\n✗ Verification failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Print summary
    success = report.print_summary()
    
    # Return exit code
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
