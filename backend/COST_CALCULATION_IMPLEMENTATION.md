# Cost Calculation and Estimation Implementation

## Overview

This document summarizes the implementation of Task 10: Cost calculation and estimation for the AI Council Web Application.

## Implemented Components

### 1. CostCalculator Service (`app/services/cost_calculator.py`)

Calculates actual costs based on token usage from AI model executions.

**Key Features:**
- Calculate cost per subtask: `input_tokens × cost_per_input + output_tokens × cost_per_output`
- Sum costs across all subtasks for total cost
- Create detailed cost breakdowns for orchestration metadata
- Cost breakdown includes:
  - Total cost
  - Cost by subtask
  - Cost by model
  - Total input/output tokens

**Methods:**
- `calculate_subtask_cost(model_id, input_tokens, output_tokens)` - Calculate cost for a single subtask
- `calculate_total_cost(subtask_costs)` - Sum costs across all subtasks
- `create_cost_breakdown(subtask_costs)` - Generate detailed cost breakdown
- `get_model_cost_per_token(model_id)` - Get pricing for a specific model

### 2. CostEstimator Service (`app/services/cost_estimator.py`)

Estimates costs before request execution based on request length and execution mode.

**Key Features:**
- Estimate costs for all three execution modes (FAST, BALANCED, BEST_QUALITY)
- Redis caching for estimates (1 hour TTL)
- Time estimation alongside cost estimation
- Historical data-based estimation using token-per-character ratios

**Estimation Logic:**
- **Token Estimation:** ~0.25 tokens per character (4 chars per token)
- **Subtask Multipliers:**
  - FAST: 1.5x (minimal decomposition)
  - BALANCED: 3.0x (moderate decomposition)
  - BEST_QUALITY: 5.0x (maximum decomposition)
- **Output Multipliers:**
  - FAST: 1.5x input length
  - BALANCED: 2.0x input length
  - BEST_QUALITY: 3.0x input length

**Methods:**
- `estimate_cost_for_mode(request_length, execution_mode)` - Estimate cost for one mode
- `estimate_all_modes(request_length)` - Estimate costs for all modes
- `estimate_all_modes_cached(request_length)` - Cached version using Redis
- `estimate_with_time(request_length, execution_mode)` - Include time estimates
- `estimate_all_modes_with_time(request_length)` - Time estimates for all modes

### 3. CostDiscrepancyLogger Service (`app/services/cost_discrepancy_logger.py`)

Logs significant discrepancies between estimated and actual costs for estimation improvement.

**Key Features:**
- Threshold: 50% discrepancy triggers logging
- Calculates discrepancy ratio: `|actual - estimate| / estimate`
- Logs as warnings with detailed metadata
- Provides discrepancy summaries

**Methods:**
- `calculate_discrepancy_ratio(estimated_cost, actual_cost)` - Calculate discrepancy
- `should_log_discrepancy(estimated_cost, actual_cost)` - Check if exceeds threshold
- `log_discrepancy(...)` - Log the discrepancy with full context
- `check_and_log(...)` - Check and log in one call
- `get_discrepancy_summary(...)` - Get structured summary

## Property-Based Tests

### Test 1: Cost Calculation Accuracy (`test_cost_calculation_accuracy.py`)

**Property 3: Cost Calculation Accuracy**
- Validates Requirements 1.6
- 7 property tests covering:
  - Subtask cost matches manual calculation
  - Total cost equals sum of subtask costs
  - Cost breakdown total matches sum
  - Cost breakdown by model matches sum
  - Token counts aggregate correctly
  - Cost is always non-negative
  - Cost scales linearly with tokens

### Test 2: Cost Estimates Ordering (`test_cost_estimates_ordering.py`)

**Property 36: Cost Estimates for All Modes**
- Validates Requirements 18.1, 18.2, 18.3
- 7 property tests covering:
  - fast_cost ≤ balanced_cost ≤ best_quality_cost
  - All estimates are non-negative
  - All modes present in estimates
  - Estimates with time include both metrics
  - Time estimates follow same ordering
  - Individual mode matches all_modes
  - Estimates are deterministic

### Test 3: Cost Estimate Based on Length (`test_cost_estimate_based_on_length.py`)

**Property 37: Cost Estimate Based on Length**
- Validates Requirements 18.4
- 7 property tests covering:
  - Longer requests have higher estimates
  - Cost scales with length multiplier
  - Very short requests have minimal cost
  - Cost ordering is transitive
  - Cost increases monotonically
  - Time estimates increase with length
  - Cost difference proportional to length difference

### Test 4: Cost Discrepancy Logging (`test_cost_discrepancy_logging.py`)

**Property 38: Significant Cost Discrepancy Logging**
- Validates Requirements 18.5
- 9 property tests covering:
  - Discrepancies >50% should log
  - Large overestimates trigger logging
  - Large underestimates trigger logging
  - Small discrepancies don't trigger logging
  - Discrepancy ratio is symmetric
  - Exact match has zero discrepancy
  - check_and_log returns correct boolean
  - Discrepancy summary includes all fields
  - Threshold boundary at 50%

## Test Results

All 30 property-based tests pass successfully:
- 7 tests for cost calculation accuracy ✓
- 7 tests for cost estimates ordering ✓
- 7 tests for cost estimate based on length ✓
- 9 tests for cost discrepancy logging ✓

## Integration Points

### With Model Registry
- Uses `MODEL_REGISTRY` for cost-per-token pricing
- Supports all cloud AI providers (Groq, Together.ai, OpenRouter, HuggingFace)
- Handles local Ollama models (zero cost)

### With Execution Mode Config
- Uses `EXECUTION_MODE_CONFIGS` for mode-specific parameters
- Considers preferred models for each mode
- Accounts for decomposition depth differences

### With Redis
- Caches cost estimates for 1 hour
- Cache key based on request length (rounded to nearest 10)
- Graceful fallback if Redis unavailable

### With Response Model
- Cost breakdown stored in `orchestration_metadata` field
- Total cost stored in `total_cost` field
- Supports historical cost analysis

## Usage Examples

### Calculate Actual Cost

```python
from app.services.cost_calculator import CostCalculator

calculator = CostCalculator()

# Calculate cost for a single subtask
cost = calculator.calculate_subtask_cost(
    model_id="groq-llama3-70b",
    input_tokens=1000,
    output_tokens=500
)

# Calculate total cost from multiple subtasks
subtask_costs = [
    {"model_id": "groq-llama3-70b", "input_tokens": 1000, "output_tokens": 500},
    {"model_id": "together-mixtral-8x7b", "input_tokens": 800, "output_tokens": 400}
]
total_cost = calculator.calculate_total_cost(subtask_costs)

# Create detailed breakdown
breakdown = calculator.create_cost_breakdown(subtask_costs)
# Returns: {total_cost, by_subtask, by_model, total_input_tokens, total_output_tokens}
```

### Estimate Cost Before Execution

```python
from app.services.cost_estimator import CostEstimator

estimator = CostEstimator(redis_client)

# Estimate for all modes
request_length = len("What are the benefits of renewable energy?")
estimates = await estimator.estimate_all_modes_cached(request_length)
# Returns: {"fast": 0.001234, "balanced": 0.003456, "best_quality": 0.007890}

# Estimate with time
estimate = estimator.estimate_with_time(request_length, "balanced")
# Returns: {"estimated_cost": 0.003456, "estimated_time_seconds": 15.2}
```

### Log Cost Discrepancies

```python
from app.services.cost_discrepancy_logger import CostDiscrepancyLogger

logger = CostDiscrepancyLogger()

# Check and log if discrepancy exceeds 50%
was_logged = logger.check_and_log(
    request_id="req-123",
    execution_mode="balanced",
    estimated_cost=0.005,
    actual_cost=0.012,  # 140% increase - will log
    request_length=250
)

# Get discrepancy summary
summary = logger.get_discrepancy_summary(
    estimated_cost=0.005,
    actual_cost=0.012
)
# Returns: {estimated_cost, actual_cost, cost_difference, discrepancy_ratio, 
#           discrepancy_percentage, direction, exceeds_threshold, threshold}
```

## Requirements Validated

- ✅ **Requirement 1.6:** Calculate costs using actual pricing from Cloud_AI_Providers
- ✅ **Requirement 7.5:** Show cost breakdown by model and by subtask
- ✅ **Requirement 18.1:** Display estimated cost for FAST execution mode
- ✅ **Requirement 18.2:** Display estimated cost for BALANCED execution mode
- ✅ **Requirement 18.3:** Display estimated cost for BEST_QUALITY execution mode
- ✅ **Requirement 18.4:** Calculate estimates based on request length and historical data
- ✅ **Requirement 18.5:** Log when |actual - estimate| / estimate > 0.5

## Next Steps

1. Integrate CostCalculator into CouncilOrchestrationBridge to calculate actual costs
2. Add cost estimation endpoint to API (GET /api/v1/council/estimate)
3. Display cost estimates in frontend QueryInput component
4. Store cost estimates with requests for comparison
5. Create dashboard for cost discrepancy analysis
6. Implement cost limit enforcement based on execution mode configs

## Git Branch

Branch: `feature/cost-calculation`
Commit: `feat: implement cost calculation and estimation`
Status: Pushed to remote, ready for PR

## Files Created

1. `backend/app/services/cost_calculator.py` - Cost calculation service
2. `backend/app/services/cost_estimator.py` - Cost estimation service
3. `backend/app/services/cost_discrepancy_logger.py` - Discrepancy logging service
4. `backend/tests/test_cost_calculation_accuracy.py` - Property tests for calculation
5. `backend/tests/test_cost_estimates_ordering.py` - Property tests for ordering
6. `backend/tests/test_cost_estimate_based_on_length.py` - Property tests for length scaling
7. `backend/tests/test_cost_discrepancy_logging.py` - Property tests for logging

Total: 7 files, ~1600 lines of code
