## Registry & Orchestrator Architecture Summary

The current evaluation system implements a multi-component architecture that enables systematic evaluation across models, memory methods, and benchmarks. This section provides an overview of the registry pattern and orchestration components implemented in the codebase.

### Core Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Multi-Component Evaluation System                 │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│                   EvaluationOrchestrator                             │
│  • Coordinates model × memory × benchmark combinations               │
│  • Manages sequential/concurrent execution with semaphore            │
│  • Handles result aggregation and error recovery                     │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│                    ComponentRegistry                                 │
│  • Unified interface for all component types                        │
│  • Delegates to specialized registries                              │
│  • Provides factory methods and metadata access                     │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│              Specialized Component Registries                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐       │
│  │  ModelRegistry  │ │ MemoryRegistry  │ │BenchmarkRegistry│       │
│  │ ─────────────── │ │ ─────────────── │ │ ─────────────── │       │
│  │ • Ollama        │ │ • Truncation    │ │ • Nestful       │       │
│  │ • OpenRouter    │ │                 │ │ • MCPBench      │       │
│  │ • [Anthropic]*  │ │                 │ │                 │       │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘       │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│                     ResultsStorage                                   │
│  • SQLite database for persistence                                  │
│  • Immediate write-after-execution                                  │
│  • JSON export capabilities                                         │
│  • Query interface for analysis                                     │
└─────────────────────────────────────────────────────────────────────┘
```

*Note: Anthropic provider is configured in model registry but not yet implemented

### Component Details

#### 1. ComponentRegistry (Unified Interface)

**Location**: `evaluation/registries.py`  
**Purpose**: Single entry point for creating and managing all evaluation components

**Key Features**:
- **Delegation Pattern**: Routes requests to specialized registries (ModelRegistry, MemoryRegistry, BenchmarkRegistry)
- **Factory Methods**: `create_model()`, `create_memory_method()`, `create_benchmark()`
- **Registration**: `register_model()`, `register_memory_method()`, `register_benchmark()`
- **Discovery**: `get_available_components()` returns all available components
- **Metadata Access**: Component information and configuration details

**Example Usage**:
```python
registry = ComponentRegistry()

# Create components
model = registry.create_model("ollama", "llama3.2:3b")
memory = registry.create_memory_method("truncation", max_tokens=500)
benchmark = registry.create_benchmark("nestful", **kwargs)

# Discover available components
components = registry.get_available_components()
# Returns: {"models": [...], "memory_methods": [...], "benchmarks": [...]}
```

#### 1.1. Provider-Specific Model Configuration

**Location**: `evaluation/config.toml`, `evaluation/orchestrator.py`  
**Purpose**: Explicit, organized model management with easy enable/disable functionality

**Configuration Structure**:
```toml
[providers.{provider_name}]
models = [...]           # All available models for this provider
enabled_models = [...]   # Subset of models to actually use
# ... provider-specific settings (temperature, max_tokens, etc.)
```

**Key Benefits**:
1. **Clear Organization**: Models grouped by their API provider
2. **Easy Selection**: Simple enable/disable per provider section  
3. **Provider Isolation**: Each provider's models and settings are contained
4. **Validation**: Enabled models must be in the available models list
5. **Extensibility**: Adding new providers requires only new configuration section

**Example Configuration**:
```toml
[providers.ollama]
models = ["gemma3:270m", "llama3.2:3b", "llama3.1:8b", "mistral:7b"]
enabled_models = ["gemma3:270m", "llama3.2:3b"]
temperature = 0.3
max_tokens = 1000

[providers.openrouter]
models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "claude-3-sonnet"]
enabled_models = []  # No models enabled by default
temperature = 0.3
max_tokens = 1000
```

**Runtime Behavior**:
1. **Model Discovery**: System reads `enabled_models` from each provider section
2. **Validation**: Ensures all enabled models exist in the provider's `models` list
3. **Instance Creation**: Creates model instances with provider-specific configuration
4. **Execution**: Runs evaluations across all enabled models from all providers

#### 2. Specialized Registries

##### ModelRegistry
**Location**: `models/registry.py`  
**Purpose**: Manage LLM providers and model instances  
**Implemented Providers**: Ollama, OpenRouter  
**Configured Providers**: Anthropic (not yet implemented)

**Key Features**:
- Provider registration with validation
- Model catalog for known models per provider
- Factory method with optional model validation
- Warning system for unknown models

##### MemoryRegistry  
**Location**: `memory/registry.py`  
**Purpose**: Manage memory constraint methods  
**Implemented Methods**: TruncationMemory  

**Key Features**:
- Method registration and factory creation
- Metadata extraction from method instances
- Comprehensive method information API

##### BenchmarkRegistry
**Location**: `evaluation/registries.py`  
**Purpose**: Manage benchmark adapters  
**Implementation**: Basic registry structure (adapters exist but not registered)

**Current Status**: Registry structure exists but benchmark adapters (Nestful, MCPBench) are not yet registered in the system.

#### 3. EvaluationOrchestrator

**Location**: `evaluation/orchestrator.py`  
**Purpose**: Coordinate multi-component evaluation execution

**Key Responsibilities**:
- **Provider-based Model Discovery**: Parses provider configuration to create model specifications
- **Combination Generation**: Creates all model × memory × benchmark combinations
- **Execution Management**: Sequential or concurrent execution with asyncio semaphore
- **Component Integration**: Uses ComponentRegistry to instantiate components
- **Result Aggregation**: Collects and summarizes evaluation results
- **Error Handling**: Graceful failure handling with detailed error reporting
- **Immediate Persistence**: Saves results after each evaluation

**Configuration-Driven**:
```toml
# evaluation/config.toml
memory_methods = ["truncation"]
benchmarks = ["nestful"]
concurrent_evaluations = 1
```

**Execution Flow**:
1. Parse provider configuration to extract enabled model specifications
2. Generate all combinations (models × memory methods × benchmarks)
3. For each combination:
   - Create component instances via ComponentRegistry
   - Execute evaluation (currently simulated)
   - Store results immediately via ResultsStorage
4. Return comprehensive summary with success metrics

**Current Limitation**: Benchmark execution is currently simulated rather than using real benchmark adapters.

#### 4. ResultsStorage (SQLite Persistence)

**Location**: `evaluation/results.py`  
**Purpose**: Reliable, queryable storage for evaluation results

**Database Schema**:
```sql
-- Main results table
CREATE TABLE evaluation_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_provider TEXT NOT NULL,
    memory_method TEXT NOT NULL,
    benchmark TEXT NOT NULL,
    status TEXT NOT NULL,  -- 'success' or 'error'
    duration_seconds REAL,
    results_json TEXT,     -- Flexible JSON for benchmark-specific results
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Additional table for detailed results (unused)
CREATE TABLE evaluation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    FOREIGN KEY (run_id) REFERENCES evaluation_runs (id)
);
```

**Key Features**:
- **Immediate Persistence**: Results written after each evaluation (crash-resistant)
- **JSON Export**: `export_to_json()` for interoperability with analysis tools
- **Query Interface**: `query_results()` with flexible filtering
- **Summary Statistics**: Comprehensive result metadata for analysis
- **Indexed Queries**: Optimized for common query patterns

### Benchmark Adapters (Partially Implemented)

#### BenchmarkAdapter (Abstract Base)
**Location**: `evaluation/BenchmarkAdapter.py`  
**Purpose**: Define common interface for benchmark implementations

**Key Features**:
- TOML configuration loading from specific sections
- Abstract methods for `run_benchmark()` and `evaluate_result()`
- Automatic configuration validation

#### NestfulAdapter (Implemented)
**Location**: `evaluation/nestful/nestful_adapter.py`  
**Purpose**: Execute function composition tasks from Nestful dataset

**Key Features**:
- Supports multiple model types (Granite, Llama, DeepSeek)
- In-context learning with configurable examples
- Batch processing with progress tracking
- Automatic prompt formatting per model type

**Current Status**: Functional but not integrated with ComponentRegistry or EvaluationOrchestrator.

#### MCPBenchAdapter (Partially Implemented)
**Location**: `evaluation/mcp_bench/mcpbench_adapter.py`  
**Purpose**: Execute tool-using tasks from MCP Benchmark dataset

**Current Status**: Adapter structure exists but implementation details not fully complete.

### Extensibility Patterns

#### Adding New Models
```python
# 1. Implement provider in models/providers/
class NewProvider(BaseModel):
    def generate_text(self, prompt, **kwargs):
        # Implementation
        pass

# 2. Register in models/registry.py
ModelRegistry.register_provider("new_provider", NewProvider)

# 3. Use in config
[providers.new_provider]
models = ["model_name"]
enabled_models = ["model_name"]
```

#### Adding New Memory Methods
```python
# 1. Implement method in memory/methods/
class SlidingWindowMemory(BaseMemory):
    def process(self, text: str) -> str:
        # Implementation
        pass

# 2. Register in memory/registry.py
MemoryRegistry.register_method("sliding_window", SlidingWindowMemory)

# 3. Use in config
memory_methods = ["truncation", "sliding_window"]
```

#### Adding New Benchmarks
```python
# 1. Implement adapter inheriting from BenchmarkAdapter
class NewBenchmarkAdapter(BenchmarkAdapter):
    async def run_benchmark(self):
        # Implementation
        pass
    
    def evaluate_result(self, task, execution_result):
        # Implementation
        pass

# 2. Register in evaluation/registries.py
BenchmarkRegistry.register_benchmark("new_benchmark", NewBenchmarkAdapter)

# 3. Use in config
benchmarks = ["nestful", "mcpbench", "new_benchmark"]
```

### Design Principles

1. **Registry Pattern**: Centralized component discovery and creation
2. **Factory Pattern**: Consistent instantiation across component types
3. **Adapter Pattern**: Uniform interface for different benchmark types
4. **Separation of Concerns**: Clear boundaries between orchestration, execution, and storage
5. **Configuration-Driven**: TOML-based configuration for reproducible experiments
6. **Fail-Safe Persistence**: Immediate result storage prevents data loss
7. **Extensible Architecture**: New components require minimal integration effort

### Current Implementation Status

**✅ Fully Implemented**:
- ComponentRegistry with delegation pattern
- ModelRegistry (Ollama, OpenRouter providers)  
- MemoryRegistry (TruncationMemory)
- EvaluationOrchestrator with provider-based configuration
- SQLite ResultsStorage with comprehensive features
- Configuration-driven evaluation pipeline
- NestfulAdapter (functional but not integrated)

**🔄 Partially Implemented**:
- BenchmarkRegistry (structure exists, adapters not registered)
- MCPBenchAdapter (exists but incomplete)
- Benchmark integration with orchestrator (currently simulated)

**❌ Not Yet Implemented**:
- Anthropic provider (configured but not implemented)
- Real benchmark execution in orchestrator
- Adapter registration in BenchmarkRegistry
- Comprehensive error handling in benchmark adapters

**🎯 Integration Gaps**:
- Benchmark adapters exist but are not registered with BenchmarkRegistry
- EvaluationOrchestrator simulates benchmark execution instead of using real adapters
- Memory methods are created but not integrated with benchmark execution

This architecture provides a robust foundation for systematic evaluation with clear separation of concerns and extensibility patterns. The main gaps are in benchmark adapter integration, which requires connecting the existing adapters to the registry and orchestration systems.

---

## Unified Task Execution Framework (Proposed Design)

*Note: This section describes a proposed design that is not currently implemented in the codebase. The actual implementation follows the Registry & Orchestrator pattern described above.*

This section outlines the architectural design for a unified task execution framework that would standardize how tasks from both the **mcp-bench** and **nestful** datasets are executed, evaluated, and persisted. This design prioritizes **maximum control**, **extensibility**, and **data resilience** through sequential execution with immediate result persistence.

### System Architecture (Proposed)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User API Layer                               │
│  UnifiedRunner(config, models, datasets) → .run()                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                   Task Orchestration Layer                           │
│  • TaskExecutor (sequential execution logic)                         │
│  • TaskFilter (compose task groups dynamically)                     │
│  • ResultWriter (persistence to SQLite after each task)             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│              Dataset Abstraction Layer (Adapters)                    │
│  ┌──────────────────────┐      ┌──────────────────────┐             │
│  │  MCPBenchAdapter     │      │  NestfulAdapter      │             │
│  │ ─────────────────── │      │ ─────────────────── │             │
│  │ load_tasks()        │      │ load_tasks()        │             │
│  │ execute_task()      │      │ execute_task()      │             │
│  │ evaluate_result()   │      │ evaluate_result()   │             │
│  └──────────────────────┘      └──────────────────────┘             │
│           (Implements TaskAdapter Interface)                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│           Dataset-Specific Internal Logic (Re-implemented)           │
│  ┌──────────────────────┐      ┌──────────────────────┐             │
│  │  MCPBench Logic      │      │  Nestful Logic       │             │
│  │ (re-implemented)     │      │ (re-implemented)     │             │
│  └──────────────────────┘      └──────────────────────┘             │
│         LLM integration            Output parsing                    │
│         MCP connection             Function evaluation              │
└─────────────────────────────────────────────────────────────────────┘
```

### Proposed Unified Data Models

#### UnifiedTask
Standardized representation of any task from any dataset.

```python
@dataclass
class UnifiedTask:
    """
    Represents a single task from any dataset.
    
    Attributes:
        id: Unique task identifier
        source: Dataset source ("mcp-bench" or "nestful")
        description: Human-readable task description
        metadata: Dataset-specific fields (flexible dict)
        task_data: Raw task object from original dataset (for adapter reference)
    """
    id: str
    source: str
    description: str
    metadata: Dict[str, Any]
    task_data: Any  # Original task object from dataset
```

#### ExecutionContext
Holds execution-specific information passed to tasks.

```python
@dataclass
class ExecutionContext:
    """Context for executing a single task."""
    model: str
    config: Config
    task_id: str
    timestamp: datetime
    
    # Optional tracking
    max_retries: int = 1
    timeout_seconds: Optional[int] = None
```

#### TaskEvaluation
Standardized evaluation result.

```python
@dataclass
class TaskEvaluation:
    """
    Result of executing and evaluating a task.
    
    Attributes:
        task_id: Reference to task
        success: Whether task succeeded
        metrics: Dict with 'token_usage' (int), 'time_taken' (float in seconds)
        raw_output: Original output from task execution (for inspection)
        error: Error message if failed
        metadata: Any additional evaluation-specific data
    """
    task_id: str
    success: bool
    metrics: Dict[str, Any]  # {token_usage, time_taken, ...}
    raw_output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Summary

The current implementation provides a solid foundation with:

✓ **Registry Pattern**: Centralized component management  
✓ **Provider-based Configuration**: Clear model organization  
✓ **Immediate Persistence**: Crash-resistant result storage  
✓ **Extensible Architecture**: Easy addition of new components  
✓ **Separation of Concerns**: Clear component boundaries  

**Next Steps** for full functionality:
1. Register benchmark adapters with BenchmarkRegistry
2. Integrate real benchmark execution in EvaluationOrchestrator
3. Implement memory method integration with benchmark adapters
4. Complete MCPBenchAdapter implementation
5. Add Anthropic provider implementation

The proposed Unified Task Execution Framework represents a future enhancement that would provide even more standardized task handling across datasets.
