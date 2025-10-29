# Benchmark Datasets

This directory contains Git submodules for the benchmark datasets used in this research framework.

## Included Benchmarks

### 1. MCP-Bench
**Purpose:** Model Context Protocol benchmark for evaluating agent tool use  
**Original Repository:** https://github.com/Accenture/mcp-bench  
**Use Case:** Testing tool-using LLM agents with MCP-compliant servers

### 2. NESTFUL
**Purpose:** NESTFUL benchmark for nested tool composition evaluation  
**Original Repository:** https://github.com/MaxiG-ai/nestful-ollama  
**Use Case:** Evaluating agents on complex nested API calls and tool composition

### 3. Tool Retrieval Benchmark
**Purpose:** Benchmark for tool retrieval and selection capabilities  
**Original Repository:** https://github.com/mangopy/tool-retrieval-benchmark  
**Use Case:** Testing tool discovery and retrieval from large tool sets

## Working with Submodules

### Initial Setup
When cloning this repository, use:
```bash
git clone --recurse-submodules <repo-url>
```

Or if already cloned:
```bash
git submodule update --init --recursive
```

### Updating Submodules
Update all submodules to latest:
```bash
git submodule update --remote --merge
```

Update specific submodule:
```bash
cd datasets/mcp-bench
git pull origin main
cd ../..
git add datasets/mcp-bench
git commit -m "Update MCP-Bench to latest"
```

### Important Notes
- **Read-only use**: These submodules should be used in read-only mode for evaluation
- **No direct modifications**: Don't modify submodule content directly in this repo
- **Contributing**: To contribute to a benchmark, fork it separately and submit PRs to the original repos
- **Reproducibility**: For reproducible research, consider pinning submodules to specific commits

## Citation Information

When using these benchmarks in your research, please cite the original papers and repositories as specified in each submodule's documentation.
