# Context Engineering for Improved Tool Use

A research framework for improving tool-using LLM agents through context engineering techniques.

**Author:** Maximilian Graf  
**Python Version:** 3.13+

## Project Overview

This repository contains the implementation framework for researching and evaluating context engineering approaches to improve LLM agent tool use. The framework provides:

- **Model Abstraction Layer**: Unified interface for multiple LLM providers
- **Memory Enhancement**: Context engineering modules for improved tool selection and use
- **Evaluation Framework**: Integration with multiple benchmark datasets
- **Experiment Management**: Tools for running and tracking experiments

## Repository Structure

```
.
├── models/              # Model abstraction layer
│   ├── base.py         # Base model interfaces
│   ├── registry.py     # Model registry
│   └── providers/      # LLM provider implementations
├── config/             # Configuration files
├── evaluation/         # Evaluation logic and metrics
├── memory/             # Memory enhancement components
├── tests/              # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── datasets/           # Benchmark datasets (Git submodules)
    ├── mcp-bench/      # MCP-Bench benchmark
    ├── nestful/        # NESTFUL benchmark
    └── tool-retrieval/ # Tool Retrieval benchmark
```

## Installation

### Prerequisites

- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Setup Steps

1. **Clone the repository with submodules:**
   ```bash
   git clone --recurse-submodules <repo-url>
   cd context-engineering-for-improved-tool-use
   ```

   Or if already cloned without submodules:
   ```bash
   git submodule update --init --recursive
   ```

2. **Install dependencies with uv:**
   ```bash
   uv sync
   ```

3. **Activate the virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

## Dataset Submodules

This project includes three benchmark datasets as Git submodules:

- **MCP-Bench**: Model Context Protocol benchmark
- **NESTFUL**: Nested tool composition benchmark  
- **Tool Retrieval Benchmark**: Tool discovery and retrieval evaluation

See [`datasets/README.md`](datasets/README.md) for detailed information about each benchmark.

### Updating Submodules

Update all benchmarks to latest versions:
```bash
git submodule update --remote --merge
git add datasets/
git commit -m "Update dataset submodules"
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=html

# Run specific test suite
uv run pytest tests/unit/
```

### Project Structure

- **models/**: Abstraction layer for LLM providers (Ollama, OpenAI, etc.)
- **memory/**: Context engineering and memory enhancement modules
- **evaluation/**: Benchmark integration and evaluation metrics
- **config/**: Configuration management

## Usage

```python
from models.registry import ModelRegistry

# Initialize a model
model = ModelRegistry.get_model("ollama", model_name="llama2")

# Use the model
response = await model.generate("What tools are available?")
```

## Contributing

This is a research project. For contributions:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

[Add license information]

## Citation

If you use this framework in your research, please cite:

```bibtex
[Add citation information when available]
```
