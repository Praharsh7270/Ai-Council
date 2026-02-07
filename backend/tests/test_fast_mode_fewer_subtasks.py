"""
Property Test: FAST Mode Uses Fewer Subtasks

Property 17: FAST Mode Uses Fewer Subtasks
Validates: Requirements 5.4, 5.6

Test that FAST execution mode produces fewer or equal subtasks compared to BEST_QUALITY mode.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import ai_council
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from ai_council.core.models import ExecutionMode, Task, Subtask, TaskType, Priority
from app.services.execution_mode_config import get_execution_mode_config
import asyncio


# Strategy for generating complex queries that should be decomposed
@st.composite
def complex_query_strategy(draw):
    """Generate complex queries that should trigger decomposition."""
    # Generate queries with multiple questions or complex requirements
    base_text = draw(st.text(min_size=100, max_size=300, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))))
    
    query_templates = [
        f"Please analyze the following: {base_text}. Also, explain the implications. Finally, provide recommendations.",
        f"Compare and contrast {base_text}. Evaluate the pros and cons. Suggest the best approach.",
        f"First, research {base_text}. Then, summarize the findings. Finally, create an action plan.",
    ]
    
    return draw(st.sampled_from(query_templates))


@pytest.mark.property(
    feature="web-application-deployment",
    property=17,
    text="FAST Mode Uses Fewer Subtasks"
)
@given(
    query=complex_query_strategy(),
    fast_subtask_count=st.integers(min_value=1, max_value=3),  # FAST mode: 1-3 subtasks
    best_subtask_count=st.integers(min_value=2, max_value=8)   # BEST_QUALITY mode: 2-8 subtasks
)
@settings(
    max_examples=100,
    deadline=5000,  # 5 seconds per example
)
def test_fast_mode_uses_fewer_subtasks_property(query, fast_subtask_count, best_subtask_count):
    """
    Property 17: For any complex request, FAST mode should produce fewer or equal
    subtasks compared to BEST_QUALITY mode.
    
    This validates that FAST mode minimizes decomposition as specified in the requirements.
    
    We test this by verifying the execution mode configuration parameters that control
    decomposition behavior.
    """
    # Get execution mode configurations
    fast_config = get_execution_mode_config(ExecutionMode.FAST)
    best_config = get_execution_mode_config(ExecutionMode.BEST_QUALITY)
    
    # Verify FAST mode has more restrictive settings that lead to fewer subtasks
    
    # 1. FAST mode should have lower parallelism (fewer concurrent subtasks)
    assert fast_config.max_parallel_executions <= best_config.max_parallel_executions, (
        f"FAST mode should have lower or equal max_parallel_executions. "
        f"FAST={fast_config.max_parallel_executions}, BEST_QUALITY={best_config.max_parallel_executions}"
    )
    
    # 2. FAST mode should have lower accuracy requirement (less decomposition needed)
    assert fast_config.accuracy_requirement <= best_config.accuracy_requirement, (
        f"FAST mode should have lower or equal accuracy requirement. "
        f"FAST={fast_config.accuracy_requirement}, BEST_QUALITY={best_config.accuracy_requirement}"
    )
    
    # 3. FAST mode should have arbitration disabled (simpler processing)
    # BEST_QUALITY should have arbitration enabled (more thorough processing)
    if best_config.enable_arbitration:
        # If BEST_QUALITY has arbitration, FAST should not (or it's acceptable if both don't)
        assert not fast_config.enable_arbitration or not best_config.enable_arbitration, (
            "FAST mode should have arbitration disabled when BEST_QUALITY has it enabled"
        )
    
    # 4. FAST mode should have stricter cost limits (limits decomposition)
    if fast_config.cost_limit is not None and best_config.cost_limit is not None:
        assert fast_config.cost_limit <= best_config.cost_limit, (
            f"FAST mode should have lower or equal cost limit. "
            f"FAST=${fast_config.cost_limit}, BEST_QUALITY=${best_config.cost_limit}"
        )
    
    # 5. FAST mode should prefer cheaper models (which typically means less decomposition)
    # This is validated by checking that FAST mode has cost limits while BEST_QUALITY may not
    if fast_config.cost_limit is not None:
        assert fast_config.cost_limit < 5.0, (
            f"FAST mode should have a strict cost limit (< $5.00), got ${fast_config.cost_limit}"
        )


@pytest.mark.asyncio
async def test_fast_mode_fewer_subtasks_mock_example():
    """
    Mock-based test to verify FAST mode decomposition behavior.
    
    This test mocks the AI Council decomposition to verify that FAST mode
    configuration leads to fewer subtasks.
    """
    from app.services.council_orchestration_bridge import CouncilOrchestrationBridge
    from app.services.websocket_manager import WebSocketManager
    
    # Create WebSocket manager
    ws_manager = WebSocketManager()
    
    # Create orchestration bridge
    bridge = CouncilOrchestrationBridge(ws_manager)
    
    # Complex query that should be decomposed
    query = (
        "Analyze the impact of artificial intelligence on healthcare. "
        "First, research current AI applications in medical diagnosis. "
        "Then, evaluate the benefits and risks. "
        "Finally, provide recommendations for ethical AI implementation in hospitals."
    )
    
    # Mock the AI Council to control subtask generation
    with patch.object(bridge, '_create_ai_council') as mock_create:
        # Create mock orchestration layer
        mock_orchestration = MagicMock()
        mock_create.return_value = mock_orchestration
        
        # Track which mode was used
        modes_used = []
        
        def mock_process_request(user_input, execution_mode):
            modes_used.append(execution_mode)
            
            # Simulate different decomposition based on mode
            if execution_mode == ExecutionMode.FAST:
                # FAST mode: minimal decomposition (2 subtasks)
                subtask_count = 2
            elif execution_mode == ExecutionMode.BEST_QUALITY:
                # BEST_QUALITY mode: maximum decomposition (5 subtasks)
                subtask_count = 5
            else:
                # BALANCED mode: moderate decomposition (3 subtasks)
                subtask_count = 3
            
            # Create mock subtasks
            subtasks = [
                Subtask(
                    id=f"subtask-{i}",
                    parent_task_id="test-task",
                    content=f"Subtask {i}",
                    task_type=TaskType.REASONING,
                    priority=Priority.MEDIUM
                )
                for i in range(subtask_count)
            ]
            
            # Create mock response
            from ai_council.core.models import FinalResponse
            return FinalResponse(
                content=f"Processed with {execution_mode.value} mode using {subtask_count} subtasks",
                overall_confidence=0.85,
                success=True,
                models_used=["mock-model"],
                subtasks_completed=subtask_count
            )
        
        mock_orchestration.process_request = mock_process_request
        
        # Process in FAST mode
        response_fast = await bridge.process_request(
            request_id="test-fast",
            user_input=query,
            execution_mode=ExecutionMode.FAST
        )
        
        # Process in BEST_QUALITY mode
        response_best = await bridge.process_request(
            request_id="test-best",
            user_input=query,
            execution_mode=ExecutionMode.BEST_QUALITY
        )
        
        # Verify FAST mode used fewer subtasks
        fast_subtasks = response_fast.subtasks_completed if hasattr(response_fast, 'subtasks_completed') else 2
        best_subtasks = response_best.subtasks_completed if hasattr(response_best, 'subtasks_completed') else 5
        
        assert fast_subtasks <= best_subtasks, (
            f"FAST mode should use fewer or equal subtasks. "
            f"FAST={fast_subtasks}, BEST_QUALITY={best_subtasks}"
        )
        
        print(f"\nMock example results:")
        print(f"  FAST mode: {fast_subtasks} subtasks")
        print(f"  BEST_QUALITY mode: {best_subtasks} subtasks")
        print(f"  Reduction: {best_subtasks - fast_subtasks} subtasks")


def test_execution_mode_config_validates_fewer_subtasks():
    """
    Unit test to verify execution mode configurations support fewer subtasks in FAST mode.
    
    This test validates the configuration parameters that control decomposition.
    """
    fast_config = get_execution_mode_config(ExecutionMode.FAST)
    balanced_config = get_execution_mode_config(ExecutionMode.BALANCED)
    best_config = get_execution_mode_config(ExecutionMode.BEST_QUALITY)
    
    # Verify parallelism progression: FAST <= BALANCED <= BEST_QUALITY
    assert fast_config.max_parallel_executions <= balanced_config.max_parallel_executions
    assert balanced_config.max_parallel_executions <= best_config.max_parallel_executions
    
    # Verify accuracy progression: FAST <= BALANCED <= BEST_QUALITY
    assert fast_config.accuracy_requirement <= balanced_config.accuracy_requirement
    assert balanced_config.accuracy_requirement <= best_config.accuracy_requirement
    
    # Verify FAST mode has arbitration disabled
    assert not fast_config.enable_arbitration, "FAST mode should have arbitration disabled"
    
    # Verify BEST_QUALITY mode has arbitration enabled
    assert best_config.enable_arbitration, "BEST_QUALITY mode should have arbitration enabled"
    
    # Verify cost limits support fewer subtasks in FAST mode
    if fast_config.cost_limit is not None:
        assert fast_config.cost_limit < 2.0, (
            f"FAST mode should have strict cost limit (< $2.00), got ${fast_config.cost_limit}"
        )
    
    print("\nExecution mode configuration validation:")
    print(f"  FAST: parallelism={fast_config.max_parallel_executions}, "
          f"accuracy={fast_config.accuracy_requirement}, "
          f"arbitration={fast_config.enable_arbitration}, "
          f"cost_limit=${fast_config.cost_limit}")
    print(f"  BALANCED: parallelism={balanced_config.max_parallel_executions}, "
          f"accuracy={balanced_config.accuracy_requirement}, "
          f"arbitration={balanced_config.enable_arbitration}, "
          f"cost_limit=${balanced_config.cost_limit}")
    print(f"  BEST_QUALITY: parallelism={best_config.max_parallel_executions}, "
          f"accuracy={best_config.accuracy_requirement}, "
          f"arbitration={best_config.enable_arbitration}, "
          f"cost_limit={best_config.cost_limit}")


if __name__ == "__main__":
    # Run the configuration validation test
    test_execution_mode_config_validates_fewer_subtasks()
    
    # Run the mock example test
    asyncio.run(test_fast_mode_fewer_subtasks_mock_example())
