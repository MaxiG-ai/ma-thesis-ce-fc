## Registry & Orchestrator Architecture Summary

The current evaluation system implements a comprehensive multi-component architecture that enables systematic evaluation across models, memory methods, and benchmarks. This section provides an overview of the registry pattern and orchestration components implemented in the codebase.

### Core Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Multi-Component Evaluation System                 │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│                   EvaluationOrchestrator                             │
│  • Coordinates model × memory × benchmark combinations               │
│  • Manages concurrent/sequential execution                          │
│  • Handles result aggregation and reporting                         │
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
│  │ • OpenRouter    │ │ • [Future]      │ │ • MCPBench      │       │
│  │ • [Future]      │ │                 │ │ • [Future]      │       │
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
benchmark = registry.create_benchmark("nestful", dataset_path="...")

# Discover available components
components = registry.get_available_components()
# Returns: {"models": [...], "memory_methods": [...], "benchmarks": [...]}
```

#### 2. Specialized Registries

##### ModelRegistry
**Location**: `models/registry.py`  
**Purpose**: Manage LLM providers and model instances  
**Registered Components**: Ollama, OpenRouter (extensible for other providers)

##### MemoryRegistry  
**Location**: `memory/registry.py`  
**Purpose**: Manage memory constraint methods  
**Registered Components**: TruncationMemory (extensible for sliding window, attention-based, etc.)

##### BenchmarkRegistry
**Location**: `evaluation/registries.py`  
**Purpose**: Manage benchmark adapters  
**Registered Components**: Nestful, MCPBench adapters (extensible for new benchmarks)

#### 3. EvaluationOrchestrator

**Location**: `evaluation/orchestrator.py`  
**Purpose**: Coordinate multi-component evaluation execution

**Key Responsibilities**:
- **Combination Generation**: Creates all model × memory × benchmark combinations
- **Execution Management**: Sequential or concurrent execution with configurable limits
- **Component Integration**: Uses ComponentRegistry to instantiate components
- **Result Aggregation**: Collects and summarizes evaluation results
- **Error Handling**: Graceful failure handling with detailed error reporting

**Configuration-Driven**:
```toml
# evaluation/config.toml
model_names = ["llama3.2:3b", "llama3.1:8b"]
memory_methods = ["truncation"]
benchmarks = ["nestful", "mcpbench"]
concurrent_evaluations = 1
```

**Execution Flow**:
1. Parse configuration to extract component specifications
2. Generate all combinations (models × memory methods × benchmarks)
3. For each combination:
   - Create component instances via ComponentRegistry
   - Execute evaluation with proper context
   - Store results immediately via ResultsStorage
4. Return comprehensive summary with success metrics

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

-- Indexes for efficient querying
CREATE INDEX idx_model_method_benchmark ON evaluation_runs(model_name, memory_method, benchmark);
CREATE INDEX idx_timestamp ON evaluation_runs(timestamp);
```

**Key Features**:
- **Immediate Persistence**: Results written after each evaluation (crash-resistant)
- **JSON Export**: `export_to_json()` for interoperability with analysis tools
- **Query Interface**: `query_results()` with flexible filtering
- **Metadata Storage**: Comprehensive result metadata for analysis

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
model_names = ["new_provider:model_name"]
```

#### Adding New Memory Methods
```python
# 1. Implement method in memory/methods/
class SlidingWindowMemory(BaseMemoryMethod):
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
# 1. Implement adapter
class NewBenchmarkAdapter(BenchmarkAdapter):
    def run_evaluation(self, model, memory_method, config):
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

**✅ Implemented Components**:
- ComponentRegistry with full delegation
- ModelRegistry (Ollama, OpenRouter providers)  
- MemoryRegistry (TruncationMemory)
- BenchmarkRegistry (Nestful, MCPBench adapters)
- EvaluationOrchestrator with multi-component support
- SQLite ResultsStorage with JSON export
- Configuration-driven evaluation pipeline

**🔄 Integration Points**:
- Memory methods integrate with all benchmark types
- Model providers work across all benchmarks  
- Results storage captures all evaluation combinations
- Configuration supports flexible component specification

This architecture provides a robust foundation for systematic evaluation across multiple dimensions while maintaining extensibility for future research directions.

---

## Overview

This document outlines the architectural design for a unified task execution framework that standardizes how tasks from both the **mcp-bench** and **nestful** datasets are executed, evaluated, and persisted. The design prioritizes **maximum control**, **extensibility**, and **data resilience** through sequential execution with immediate result persistence.

---

## System Architecture

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

---

## Core Components

### 1. Unified Configuration Layer

**Purpose**: Load and validate execution configuration from TOML.

**Responsibilities**:
- Parse TOML configuration
- Validate required fields
- Provide configuration object to runners
- Handle environment variable expansion (optional)

**Configuration Structure** (example `config.toml`):
```toml
[execution]
output_db = "results.db"
sequential = true
log_level = "info"

[models]
primary = "gpt-4"

[paths]
# Optional: override dataset paths if needed
mcp_bench_path = "/path/to/mcp-bench"
nestful_path = "/path/to/nestful"
```

**Component**: `ConfigLoader`
```python
class ConfigLoader:
    @staticmethod
    def load(config_path: str) -> Config:
        """Load and validate TOML configuration"""
        pass
    
    def get(self, key: str, default=None):
        """Get configuration value by dot notation"""
        pass
```

---

### 2. Unified Data Models

**Purpose**: Define common abstractions that all datasets adhere to.

#### 2.1 UnifiedTask
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

#### 2.2 ExecutionContext
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

#### 2.3 TaskEvaluation
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

---

### 3. Task Abstraction Layer (Adapter Pattern)

**Purpose**: Normalize both datasets to a unified interface while maintaining control over execution logic.

**Design Decision**: Implement core logic from scratch (Option B) rather than wrapping existing code. This enables:
- Precise control over task execution flow
- Standardized metrics collection (token usage, timing)
- Consistent error handling
- Future optimization without modifying original codebases

#### 3.1 TaskAdapter Interface

```python
class TaskAdapter(ABC):
    """
    Abstract base class for dataset-specific adapters.
    
    Each adapter is responsible for:
    1. Loading tasks from its dataset
    2. Executing tasks with a given model
    3. Evaluating and scoring results
    """
    
    @abstractmethod
    def load_tasks(self, dataset_path: str, filters: Optional[Dict] = None) -> List[UnifiedTask]:
        """
        Load tasks from the dataset.
        
        Args:
            dataset_path: Path to dataset directory/file
            filters: Optional filter criteria (dataset-specific)
        
        Returns:
            List of UnifiedTask objects
        """
        pass
    
    @abstractmethod
    def execute_task(
        self,
        task: UnifiedTask,
        context: ExecutionContext
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Execute a single task using the specified model.
        
        Args:
            task: The task to execute
            context: Execution context (model, config, etc.)
        
        Returns:
            Tuple of (raw_output, metrics_dict) where metrics_dict contains:
            - token_usage: int (total tokens used)
            - time_taken: float (seconds)
            - Any other relevant metrics
        """
        pass
    
    @abstractmethod
    def evaluate_result(
        self,
        task: UnifiedTask,
        raw_output: Any
    ) -> bool:
        """
        Evaluate whether the task result is correct.
        
        Args:
            task: The task that was executed
            raw_output: The raw output from execution
        
        Returns:
            Boolean indicating success
        """
        pass
```

#### 3.2 MCPBenchAdapter

**Responsibilities**:
- Load tasks from mcp-bench JSON files
- Connect to MCP servers
- Execute tasks using LLM with tool access
- Evaluate results against success criteria
- Track token usage from LLM calls
- Track execution time

**Key Methods**:

```python
class MCPBenchAdapter(TaskAdapter):
    def __init__(self, llm_factory: LLMFactory):
        """Initialize with LLM provider factory."""
        self.llm_factory = llm_factory
    
    def load_tasks(
        self,
        dataset_path: str,
        filters: Optional[Dict] = None
    ) -> List[UnifiedTask]:
        """
        Load from mcp-bench JSON files.
        
        Handles:
        - Multiple task format files (single, multi_2server, multi_3server)
        - Parsing JSON structure
        - Extracting servers, questions, success criteria
        - Applying optional filters (by server_name, task_type, etc.)
        """
        pass
    
    def execute_task(
        self,
        task: UnifiedTask,
        context: ExecutionContext
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Execute mcp-bench task.
        
        Flow:
        1. Extract required MCP servers from task metadata
        2. Start/connect to MCP server instances
        3. Initialize LLM with server tools
        4. Run agentic loop until completion or max iterations
        5. Track tokens from LLM provider
        6. Return final agent output and metrics
        """
        pass
    
    def evaluate_result(
        self,
        task: UnifiedTask,
        raw_output: Any
    ) -> bool:
        """
        Check if output satisfies success criteria.
        
        Handles:
        - String matching against expected results
        - Custom validation logic from task metadata
        - Partial success scenarios
        """
        pass
```

**Internal Dependencies** (re-implement):
- MCP server connection/management (from `mcp_modules/`)
- LLM integration (from `llm/factory.py`)
- Agent execution loop logic (from `agent/executor.py`)

#### 3.3 NestfulAdapter

**Responsibilities**:
- Load tasks from nestful JSONL dataset
- Parse instructions and available functions
- Execute LLM to generate function chains
- Evaluate correctness of generated chains
- Track token usage and execution time

**Key Methods**:

```python
class NestfulAdapter(TaskAdapter):
    def __init__(self, llm_factory: LLMFactory):
        """Initialize with LLM provider factory."""
        self.llm_factory = llm_factory
    
    def load_tasks(
        self,
        dataset_path: str,
        filters: Optional[Dict] = None
    ) -> List[UnifiedTask]:
        """
        Load from nestful JSONL file.
        
        Handles:
        - Reading JSONL format
        - Extracting instructions, available functions, expected output
        - Applying optional filters (by difficulty, function_type, etc.)
        - Normalizing to UnifiedTask format
        """
        pass
    
    def execute_task(
        self,
        task: UnifiedTask,
        context: ExecutionContext
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Execute nestful task (function chain generation).
        
        Flow:
        1. Format instruction with available functions context
        2. Call LLM to generate function chain
        3. Parse LLM output to extract chain specification
        4. Execute function chain (or score parsing correctness)
        5. Track tokens and execution time
        6. Return function chain and metrics
        """
        pass
    
    def evaluate_result(
        self,
        task: UnifiedTask,
        raw_output: Any
    ) -> bool:
        """
        Evaluate function chain correctness.
        
        Handles:
        - Parsing output format
        - Comparing against ground-truth chains
        - Partial credit scenarios
        - Execution correctness vs. chain structure correctness
        """
        pass
```

**Internal Dependencies** (re-implement):
- Output parsing logic (from `output_parsers.py`)
- Scoring logic (from `scorer.py`)
- LLM integration (compatible with both datasets)

---

### 4. Task Orchestration Layer

**Purpose**: Coordinate task execution, filtering, and result persistence.

#### 4.1 TaskFilter

Enables dynamic composition of task groups at runtime.

```python
class TaskFilter:
    """
    Builds and applies filters to task collections.
    
    Supports:
    - Filtering by dataset
    - Filtering by metadata fields
    - Combining multiple filters (AND logic)
    - Limiting result count
    """
    
    def __init__(self, tasks: List[UnifiedTask]):
        """Initialize with task list."""
        self.tasks = tasks
        self.predicates = []
    
    def by_dataset(self, source: str) -> 'TaskFilter':
        """Filter tasks from specific dataset."""
        pass
    
    def by_metadata(self, key: str, value: Any) -> 'TaskFilter':
        """Filter by metadata field equality."""
        pass
    
    def by_metadata_in(self, key: str, values: List[Any]) -> 'TaskFilter':
        """Filter by metadata field membership."""
        pass
    
    def limit(self, n: int) -> 'TaskFilter':
        """Keep only first n tasks."""
        pass
    
    def apply(self) -> List[UnifiedTask]:
        """Apply all filters and return result."""
        pass
```

**Usage Example**:
```python
filtered = TaskFilter(all_tasks) \
    .by_dataset("mcp-bench") \
    .by_metadata_in("servers", ["weather", "time"]) \
    .limit(10) \
    .apply()
```

#### 4.2 ResultWriter

Writes execution results to SQLite immediately after each task completes.

```python
class ResultWriter:
    """
    Persists execution results to SQLite database.
    
    Responsibilities:
    - Create database schema on first run
    - Write task metadata (if not exists)
    - Write execution results immediately after completion
    - Handle concurrent writes safely
    """
    
    def __init__(self, db_path: str):
        """Initialize database connection."""
        self.db_path = db_path
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Create tables if they don't exist."""
        pass
    
    def write_task(self, task: UnifiedTask):
        """Write task metadata to database."""
        pass
    
    def write_execution(self, evaluation: TaskEvaluation):
        """Write execution result immediately."""
        pass
    
    def write_batch(self, evaluations: List[TaskEvaluation]):
        """Write multiple results (optional batch mode)."""
        pass
```

**Database Schema**:
```sql
-- Task catalog (immutable after first insertion)
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    description TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Execution results (one row per task execution)
CREATE TABLE executions (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    model TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    token_usage INTEGER,
    time_taken REAL,
    output JSON,
    error TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(task_id) REFERENCES tasks(id)
);

-- Index for common queries
CREATE INDEX idx_executions_task_model ON executions(task_id, model);
CREATE INDEX idx_executions_timestamp ON executions(timestamp);
```

**Design Rationale**: Write after each task to prevent data loss if execution crashes.

#### 4.3 TaskExecutor

Orchestrates sequential execution of tasks.

```python
class TaskExecutor:
    """
    Executes tasks sequentially, evaluates results, and persists to database.
    
    Ensures:
    - Sequential execution (no parallelization)
    - Consistent error handling
    - Metrics tracking
    - Immediate result persistence
    """
    
    def __init__(
        self,
        adapters: Dict[str, TaskAdapter],
        result_writer: ResultWriter,
        config: Config
    ):
        """
        Initialize executor.
        
        Args:
            adapters: Dict mapping dataset source to adapter instance
            result_writer: Database writer
            config: Execution configuration
        """
        self.adapters = adapters
        self.result_writer = result_writer
        self.config = config
    
    def execute(
        self,
        tasks: List[UnifiedTask],
        model: str
    ) -> ExecutionReport:
        """
        Execute all tasks sequentially.
        
        Args:
            tasks: List of UnifiedTask to execute
            model: Model to use for execution
        
        Returns:
            ExecutionReport with summary statistics
        
        Flow:
        1. For each task:
           a. Get appropriate adapter by task.source
           b. Create ExecutionContext
           c. Call adapter.execute_task()
           d. Call adapter.evaluate_result()
           e. Construct TaskEvaluation
           f. Call result_writer.write_execution()
           g. Log metrics
           h. Continue to next task (no stopping on error)
        2. Return summary report
        """
        pass
```

**ExecutionReport**:
```python
@dataclass
class ExecutionReport:
    """Summary of execution run."""
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    total_tokens: int
    total_time: float
    start_timestamp: datetime
    end_timestamp: datetime
    errors: List[str]
    
    def success_rate(self) -> float:
        """Calculate success percentage."""
        pass
```

---

### 5. User-Facing API Layer

**Purpose**: Provide intuitive, chainable API for defining and running experiments.

#### 5.1 UnifiedRunner

Main entry point for users.

```python
class UnifiedRunner:
    """
    High-level API for defining and executing unified tasks.
    
    Responsibilities:
    - Initialize adapters and infrastructure
    - Register datasets
    - Coordinate execution
    - Return results
    """
    
    def __init__(self, config_path: str, model: str):
        """
        Initialize runner.
        
        Args:
            config_path: Path to TOML config file
            model: Model identifier (e.g., "gpt-4", "claude-3", "ollama-mistral")
        """
        self.config = ConfigLoader.load(config_path)
        self.model = model
        self.task_groups: Dict[str, TaskGroup] = {}
        self._initialize_adapters()
    
    def _initialize_adapters(self):
        """Create adapter instances for each dataset."""
        # Initialize LLM factory with config
        # Initialize MCPBenchAdapter
        # Initialize NestfulAdapter
        pass
    
    def add_dataset(
        self,
        dataset_name: str,
        dataset_path: str
    ) -> 'TaskGroup':
        """
        Register a dataset for execution.
        
        Args:
            dataset_name: Identifier ("mcp-bench", "nestful", etc.)
            dataset_path: Path to dataset
        
        Returns:
            TaskGroup for chaining filters
        """
        pass
    
    def run(self) -> ExecutionReport:
        """
        Execute all registered task groups sequentially.
        
        Returns:
            ExecutionReport with results
        """
        pass
```

#### 5.2 TaskGroup

Returned by `add_dataset()`, enables chainable filtering.

```python
class TaskGroup:
    """
    Represents a collection of tasks from a single dataset.
    
    Supports:
    - Dynamic filtering
    - Limiting number of tasks
    - Chaining multiple filters
    """
    
    def __init__(
        self,
        dataset_name: str,
        dataset_path: str,
        adapter: TaskAdapter
    ):
        """Initialize task group."""
        self.dataset_name = dataset_name
        self.dataset_path = dataset_path
        self.adapter = adapter
        self.filters = {}
        self._tasks = None
    
    def filter_by(self, **criteria) -> 'TaskGroup':
        """
        Apply filter criterion to tasks.
        
        Args:
            **criteria: Dataset-specific filter criteria
            Example: filter_by(servers=['weather', 'time'])
        
        Returns:
            Self for chaining
        """
        pass
    
    def limit(self, n: int) -> 'TaskGroup':
        """
        Limit results to first n tasks.
        
        Args:
            n: Maximum number of tasks
        
        Returns:
            Self for chaining
        """
        pass
    
    def _load_tasks(self) -> List[UnifiedTask]:
        """Load and cache tasks with filters applied."""
        pass
```

---

## Execution Flow

### Standard Execution Sequence

```
1. User calls:
   runner = UnifiedRunner("config.toml", model="gpt-4")
   
2. Runner initialization:
   - Load config from TOML
   - Initialize adapters (MCPBenchAdapter, NestfulAdapter)
   - Create ResultWriter with output_db path
   
3. User registers datasets:
   runner.add_dataset("mcp-bench", "/path/to/mcp-bench") \
       .filter_by(servers=['weather', 'time'])
   runner.add_dataset("nestful", "/path/to/nestful") \
       .limit(10)
   
4. User calls:
   report = runner.run()
   
5. Execution logic:
   a. For each TaskGroup registered:
      i. Load tasks via adapter.load_tasks()
      ii. Apply filters via TaskFilter
   
   b. Combine all filtered tasks into single list
   
   c. Create TaskExecutor
   
   d. For each task (sequential):
      i. Create ExecutionContext(model=model, config=config, task_id=task.id)
      
      ii. Get adapter for task.source
      
      iii. Call adapter.execute_task(task, context)
           Returns: (raw_output, metrics_dict)
      
      iv. Call adapter.evaluate_result(task, raw_output)
          Returns: bool (success)
      
      v. Create TaskEvaluation(task_id, success, metrics, raw_output)
      
      vi. Call result_writer.write_execution(evaluation)
          ** Writes to SQLite immediately **
      
      vii. Log: "[Task X/Y] source=mcp-bench id=abc success=true tokens=1234 time=2.3s"
      
      viii. Continue to next task (no stopping on failure)
   
   e. Return ExecutionReport(summary stats)
   
6. User receives report with:
   - Total/successful/failed task counts
   - Total tokens and time
   - Success rate
   - Any critical errors
```

---

## Data Persistence Strategy

### Why Immediate Persistence?

- **Crash resilience**: Partial results saved if process dies mid-execution
- **Memory efficiency**: No accumulation of results in RAM
- **Audit trail**: Exact execution order recorded via timestamps
- **Non-blocking**: Writes are fast (single table inserts)

### Database Access Patterns

**For result retrieval** (post-execution):
```python
# Example queries
import sqlite3

conn = sqlite3.connect("results.db")
conn.row_factory = sqlite3.Row

# Success rate by dataset
cur = conn.execute("""
    SELECT 
        t.source,
        COUNT(*) as total,
        SUM(CASE WHEN e.success THEN 1 ELSE 0 END) as successful
    FROM executions e
    JOIN tasks t ON e.task_id = t.id
    WHERE e.model = ?
    GROUP BY t.source
""", ("gpt-4",))

# Average tokens by dataset and model
cur = conn.execute("""
    SELECT 
        t.source,
        e.model,
        AVG(e.token_usage) as avg_tokens,
        AVG(e.time_taken) as avg_time
    FROM executions e
    JOIN tasks t ON e.task_id = t.id
    GROUP BY t.source, e.model
""")
```

---

## Integration Points

### With Existing Codebases

Since we're re-implementing logic (Option B), integration is **minimal**:

#### From mcp-bench, leverage:
- Task file formats (JSON structure)
- MCP server specifications and configurations
- Reference implementations for evaluation logic
- Server manager implementations for connection handling

#### From nestful, leverage:
- Task file formats (JSONL structure)
- Function definitions and schemas
- Reference implementations for evaluation metrics
- Instruction templates

### LLM Integration

The `UnifiedRunner` accepts a model identifier and uses an LLM factory pattern:

```python
# To add support for new LLM providers:
# 1. Implement LLMProvider interface
# 2. Register in LLMFactory
# 3. Pass model string to UnifiedRunner

llm_factory.register("gpt-4", OpenAIProvider)
llm_factory.register("claude-3", AnthropicProvider)
llm_factory.register("ollama-mistral", OllamaProvider)

# UnifiedRunner uses factory internally
runner = UnifiedRunner("config.toml", model="gpt-4")
```

---

## Development Phases

### Phase 1: Foundation (Core Architecture)
**Goals**: Establish unified framework

1. **Data Models** (`unified_models.py`)
   - UnifiedTask
   - ExecutionContext
   - TaskEvaluation
   - ExecutionReport

2. **Adapter Pattern** (`adapters/base.py`, `adapters/mcp_bench.py`, `adapters/nestful.py`)
   - TaskAdapter abstract base
   - MCPBenchAdapter (re-implemented logic)
   - NestfulAdapter (re-implemented logic)

3. **Configuration** (`config.py`)
   - ConfigLoader
   - TOML parsing

4. **Orchestration** (`orchestration.py`)
   - TaskFilter
   - TaskExecutor
   - ResultWriter
   - DatabaseSchema

5. **API Layer** (`runner.py`)
   - UnifiedRunner
   - TaskGroup

### Phase 2: Enhancement (Future)
- MetaRunner for model comparison
- Advanced query interface over SQLite results
- Task grouping definitions (saved configs)
- Performance optimizations
- Optional parallelization (structure for future)
- Caching mechanisms for frequently-accessed tasks

---

## Design Patterns & Principles

| Pattern/Principle          | Implementation                                            |
| -------------------------- | --------------------------------------------------------- |
| **Adapter Pattern**        | TaskAdapter interface normalizes different datasets       |
| **Separation of Concerns** | Orchestration, execution, persistence are distinct layers |
| **Single Responsibility**  | Each class has one clear purpose                          |
| **Extensibility**          | New datasets require only new adapter implementation      |
| **Fail-Safe Persistence**  | Results written immediately, no batch loss                |
| **Sequential Execution**   | Simple, deterministic, easy to debug                      |
| **Configuration as Code**  | TOML for environment, API for experiments                 |

---

## Error Handling Strategy

### Execution-Level Errors
- Catch exceptions during task execution
- Log error with task_id and timestamp
- Store error message in database
- Mark task as failed (success=False)
- Continue to next task (no stopping)

### System-Level Errors
- Database write failure: Log to stderr, but continue (optional: retry)
- Adapter initialization failure: Raise and halt
- Config parsing failure: Raise and halt
- Missing dataset path: Raise and halt

### Retry Logic (Optional Future)
- Configurable retry count per task
- Exponential backoff for transient failures
- Log retry attempts

---

## Future Extensibility

### Adding New Datasets

1. Create new adapter class inheriting from `TaskAdapter`
2. Implement three methods:
   - `load_tasks()`: Parse dataset format → UnifiedTask list
   - `execute_task()`: Run task with model → (output, metrics)
   - `evaluate_result()`: Score output → bool
3. Register adapter in UnifiedRunner
4. Done! Existing orchestration handles the rest

Example:
```python
class MyDatasetAdapter(TaskAdapter):
    def load_tasks(self, dataset_path, filters=None):
        # Parse my dataset format
        pass
    
    def execute_task(self, task, context):
        # Execute with model
        pass
    
    def evaluate_result(self, task, raw_output):
        # Score result
        pass

# In UnifiedRunner
runner._adapters["my-dataset"] = MyDatasetAdapter(llm_factory)
```

### Adding New LLM Providers

1. Implement LLMProvider interface
2. Handle token counting and response tracking
3. Register in LLMFactory
4. Pass model string to UnifiedRunner

### Adding Metrics

1. Extend `metrics` dict in TaskEvaluation
2. Populate in adapter's `execute_task()` return value
3. All downstream code (storage, reporting) automatically captures

---

## Summary

This architecture provides:

✓ **Unified Interface**: Single API for both datasets  
✓ **Maximum Control**: Per-task filtering, model assignment, execution tracking  
✓ **Extensibility**: Add datasets by implementing one interface  
✓ **Resilience**: Immediate persistence prevents data loss  
✓ **Clarity**: Layered design with clear responsibilities  
✓ **Auditability**: Complete execution history in SQLite  
✓ **Future-Ready**: Structure supports MetaRunner and optimization  

Use this document as a development guide. Each phase builds on the previous, and the modular design allows implementation in any order once dependencies are clear.