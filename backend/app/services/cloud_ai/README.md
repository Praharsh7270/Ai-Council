# Cloud AI Provider Integration

This module provides a unified interface for both cloud AI providers and local Ollama models, supporting different deployment scenarios.

## Deployment Modes

The system supports three deployment modes:

### 1. Cloud Mode (Production)
- Uses cloud AI providers: Groq, Together.ai, OpenRouter, HuggingFace
- Requires API keys for each provider
- Best for production deployments
- Pay-per-use pricing

**Configuration:**
```bash
AI_DEPLOYMENT_MODE=cloud
GROQ_API_KEY=your_groq_key
TOGETHER_API_KEY=your_together_key
OPENROUTER_API_KEY=your_openrouter_key
HUGGINGFACE_API_KEY=your_huggingface_key
```

### 2. Local Mode (Development)
- Uses Ollama for local inference
- Free to use, runs on your hardware
- Best for local development and testing
- Requires Ollama to be installed and running

**Configuration:**
```bash
AI_DEPLOYMENT_MODE=local
OLLAMA_BASE_URL=http://localhost:11434  # Optional, defaults to localhost
```

**Install Ollama:**
```bash
# Visit https://ollama.ai to download and install
# Then pull models:
ollama pull llama2
ollama pull mistral
ollama pull codellama
```

### 3. Hybrid Mode (Flexible)
- Uses both cloud and local providers
- Prefers cloud providers, falls back to Ollama
- Best for development teams that want flexibility
- Useful for cost optimization

**Configuration:**
```bash
AI_DEPLOYMENT_MODE=hybrid
# Configure both cloud API keys and Ollama
```

## Available Models

### Cloud Models (Production)
- **groq-llama3-70b**: Fast reasoning and research
- **groq-mixtral-8x7b**: Fast reasoning and creative output
- **together-mixtral-8x7b**: Reasoning and code generation
- **together-llama2-70b**: Research and creative output
- **openrouter-claude-3-sonnet**: Premium quality, all tasks
- **openrouter-gpt4-turbo**: Premium quality, code and debugging
- **huggingface-mistral-7b**: Cost-effective reasoning

### Local Models (Development)
- **ollama-llama2**: General purpose reasoning
- **ollama-mistral**: Code generation and reasoning
- **ollama-codellama**: Specialized for code tasks

## Usage

### Basic Usage

```python
from app.services.cloud_ai import CloudAIAdapter

# Cloud provider
adapter = CloudAIAdapter(
    provider="groq",
    model_id="llama3-70b-8192",
    api_key=os.getenv("GROQ_API_KEY")
)

# Local provider
adapter = CloudAIAdapter(
    provider="ollama",
    model_id="llama2",
    api_key=""  # Not needed for Ollama
)

# Generate response
response = adapter.generate_response("What is AI?")
```

### Model Selection

```python
from app.services.cloud_ai.model_registry import (
    get_models_for_task_type,
    get_cheapest_model_for_task,
    get_fastest_model_for_task,
    get_cloud_models_only,
    get_local_models_only,
)
from ai_council.core.models import TaskType

# Get all models for a task
models = get_models_for_task_type(TaskType.CODE_GENERATION)

# Get only cloud models
cloud_models = get_cloud_models_only()

# Get only local models
local_models = get_local_models_only()

# Get cheapest model for a task
cheapest = get_cheapest_model_for_task(TaskType.REASONING)
```

### Circuit Breaker

The system includes automatic circuit breaker protection for all providers:

```python
from app.services.cloud_ai.circuit_breaker import get_circuit_breaker

cb = get_circuit_breaker()

# Check provider availability
if cb.is_available("groq"):
    # Make request
    pass

# Get circuit breaker stats
stats = cb.get_stats("groq")
print(f"State: {stats['state']}")
print(f"Failures: {stats['failure_count']}")
```

## Architecture

```
CloudAIAdapter (implements AIModel interface)
    ├── GroqClient (cloud)
    ├── TogetherClient (cloud)
    ├── OpenRouterClient (cloud)
    ├── HuggingFaceClient (cloud)
    └── OllamaClient (local)
```

## Benefits of Hybrid Approach

### For Developers
- Test features locally without API costs
- Faster iteration during development
- No internet required for basic testing
- Easy to switch between cloud and local

### For Production
- Use powerful cloud models for best quality
- Automatic failover with circuit breakers
- Cost optimization through model selection
- Scalable without hardware constraints

### For Teams
- Developers use local, staging/prod use cloud
- Consistent interface across environments
- Easy onboarding (no API keys needed initially)
- Gradual migration path

## Environment Variables

```bash
# Deployment mode
AI_DEPLOYMENT_MODE=cloud|local|hybrid  # Default: cloud

# Cloud provider API keys
GROQ_API_KEY=your_key_here
TOGETHER_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
HUGGINGFACE_API_KEY=your_key_here

# Ollama configuration (for local/hybrid mode)
OLLAMA_BASE_URL=http://localhost:11434  # Default
```

## Testing

Run tests for all providers:

```bash
# Test cloud AI response parsing
python -m pytest tests/test_cloud_ai_response_parsing.py -v

# Test model routing
python -m pytest tests/test_model_routing.py -v

# Test circuit breaker
python -m pytest tests/test_circuit_breaker.py -v
```

## Migration Guide

### From Ollama-only to Hybrid

1. Keep your existing Ollama setup
2. Add cloud API keys to `.env`
3. Set `AI_DEPLOYMENT_MODE=hybrid`
4. System will prefer cloud but fallback to Ollama

### From Cloud-only to Hybrid

1. Install Ollama locally
2. Pull required models
3. Set `AI_DEPLOYMENT_MODE=hybrid`
4. System will use Ollama as fallback

## Troubleshooting

### Ollama not detected
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

### Cloud provider failures
- Check API keys are set correctly
- Verify API key has sufficient credits
- Check circuit breaker status
- Review logs for specific errors

### Model not found
```bash
# For Ollama, pull the model first
ollama pull llama2
ollama pull mistral
```
