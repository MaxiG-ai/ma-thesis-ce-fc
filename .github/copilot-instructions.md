## Copilot / AI agent instructions — Context Engineering repo

This file gives concise, actionable guidance for an AI coding agent to be productive in this repository.

### Must-follow rules
- Always run project commands through uv. Never call `python`, `pytest`, or similar directly.
  - Correct: `uv run pytest`
  - Incorrect: `pytest`
- Python runtime: 3.13+. Use the project venv if present (`source .venv/bin/activate`).
- Tests must be real `pytest` tests located under `tests/`. Do not create throwaway scripts.
- Never ever create usage_examples unless I specifically ask you to do so.

### Where to start (quick reading list)
- `AGENTS.md` — project testing and package-management rules (uv prefix, test style).
- `README.md` — high-level architecture and examples (ModelRegistry usage).
- `models/` — model abstraction layer: `models/base.py`, `models/registry.py`, `models/providers/`.
- `memory/` — memory and truncation logic (e.g., `truncation_memory.py`).
- `datasets/mcp_bench/` — benchmark integration, agent executor, MCP modules and servers.

### Project-specific workflows and examples
- Install / sync dependencies: `uv sync` (from repo root).
- Run tests:
  - All tests: `uv run pytest`
  - Unit tests only: `uv run pytest tests/unit/`
  - With coverage: `uv run pytest --cov=. --cov-report=html`
- Update dataset submodules: `git submodule update --init --recursive` and `git submodule update --remote --merge`.
- Environment variables: copy `.env.example` to `.env` and add API keys locally.

### Conventions and patterns
- Tests: use pytest-style functions, name `test_*`, prefer fixtures and `assert` statements (see `tests/unit/`).
- Model providers: add implementations in `models/providers/` and register them in `models/registry.py`.
- Agent plumbing: core agent/executor code lives under `datasets/mcp_bench/agent/` (see `executor.py`).
- MCP servers: packaged in `datasets/mcp_bench/mcp_servers/` — used by the MCP benchmark tooling.

### Integration points & external deps
- LLM providers listed in `pyproject.toml` (e.g., `ollama`, `openai`, `langchain-ollama`).
- MCP package dependency: `mcp>=1.20.0` (used throughout `datasets/mcp_bench`).
- Some tests and benchmarks may require API keys — prefer mocking in CI.

### What to avoid
- Do not run Python/test commands directly (always use `uv run ...`).
- Do not add ad-hoc verification scripts — put tests under `tests/`.
- Avoid changing dataset submodules in PRs unless necessary and noted explicitly.

### Quick references (files to open)
- `AGENTS.md` — rules for tests and uv usage.
- `README.md` — architecture overview and example usage.
- `models/registry.py` and `models/providers/` — model wiring.
- `datasets/mcp_bench/agent/executor.py` and `execution_context.py` — agent flow.
- `memory/truncation_memory.py` and `tests/unit/test_memory_truncation.py` — memory behavior and tests.

If this looks good I can commit this file now and run a quick test (lint/tests) per repo rules; or iterate on wording/length per your preference.
