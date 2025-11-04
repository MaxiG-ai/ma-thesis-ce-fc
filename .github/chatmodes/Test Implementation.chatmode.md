---
description: 'Creation of the tests for TDD'
tools: ['runCommands', 'runTasks', 'edit', 'runNotebooks', 'search', 'new', 'extensions', 'todos', 'runTests', 'usages', 'vscodeAPI', 'problems', 'changes', 'testFailure', 'openSimpleBrowser', 'fetch', 'githubRepo', 'ms-python.python/getPythonEnvironmentInfo', 'ms-python.python/getPythonExecutableCommand', 'ms-python.python/installPythonPackage', 'ms-python.python/configurePythonEnvironment']
---
# Test implementation  

Implement the tests, which are described in the provided file using the Test-Driven Development (TDD) methodology. 

Keep in mind the testing principles:

- Always run project commands through uv. Never call `python`, `pytest`, or similar directly.
  - Correct: `uv run pytest`
  - Incorrect: `pytest`
- Python runtime: 3.13+. Use the project venv if present (`source .venv/bin/activate`).
- Tests must be real `pytest` tests located under `tests/`. Do not create throwaway scripts.
- be thoughtful about the tests you create
    - avoid duplicate testing of functionality
    - comment the tests, so that others can understand easily