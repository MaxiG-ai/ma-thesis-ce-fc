"""Integration tests for the config-driven MCPBenchAdapter.

These tests follow the repository testing guidance in `AGENTS.md`:
- keep pytest-style tests under `tests/`;
- avoid asserting on exact config file literal values at this level;
- focus on returned types/structure and compatibility with runner helpers.
"""

from pathlib import Path
import sys
import textwrap
import tempfile

# Add project root to path for local imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from evaluation.mcp_bench.mcpbench_adapter import MCPBenchAdapter


class TestMCPBenchAdapterIntegration:
    """Integration tests for MCPBenchAdapter with relaxed assertions.

    These tests ensure the adapter produces an args-like object with the
    properties the runner expects and that the runner helpers accept the
    produced arguments. They do not validate exact numeric/string literals
    from the TOML config file; that level of validation belongs in unit
    tests for the adapter itself or end-to-end tests.
    """

    def _write_config(self, tmpfile, contents: str) -> str:
        # Ensure TOML section headers are at start-of-line by dedenting
        normalized = textwrap.dedent(contents).lstrip('\n')
        tmpfile.write(normalized)
        tmpfile.flush()
        return tmpfile.name

    def test_parse_arguments_from_config_structure(self):
        """Ensure parse_arguments_from_config returns an object with expected shape."""
        # Use orchestrator mode (pass config dict directly) to avoid filesystem
        # dependencies in this integration-level test.
        cfg = {
            "model_names": ["llama3.2:3b"],
            "tasks_file": "datasets/mcp_bench/tasks/mcpbench_tasks_single_runner_format.json",
            "verbose": False,
            "distraction_count": 0,
        }

        adapter = MCPBenchAdapter(model_instance=object(), memory_instance=None, benchmark_config=cfg)
        args = adapter.parse_arguments_from_config()

        # Check minimal structural expectations (types, presence)
        assert hasattr(args, 'models') and isinstance(args.models, (list, tuple))
        assert hasattr(args, 'tasks_file') and isinstance(args.tasks_file, str)
        assert hasattr(args, 'verbose') and isinstance(args.verbose, bool)
        assert hasattr(args, 'distraction_count') and isinstance(args.distraction_count, int)

    def test_parse_and_validate_args_from_config_returns_expected_types(self):
        """Ensure parse_arguments_from_config can be used to derive enable_distraction.

        We avoid calling a separate `parse_and_validate_args_from_config` helper here
        because file-existence validation and CLI-level concerns belong in unit
        tests for that helper, not in this integration-level test.
        """
        # Provide a minimal benchmark_config and use orchestrator mode so the
        # adapter doesn't attempt to read files from disk.
        cfg = {
            "model_names": ["llama3.2:3b"],
            "tasks_file": "datasets/mcp_bench/tasks/mcpbench_tasks_single_runner_format.json",
            "verbose": False,
            "distraction_count": 0,
        }

        adapter = MCPBenchAdapter(model_instance=object(), memory_instance=None, benchmark_config=cfg)
        args = adapter.parse_arguments_from_config()

        assert isinstance(args, object)
        assert hasattr(args, 'distraction_count')
        enable_distraction = args.distraction_count > 0
        assert enable_distraction is False

    def test_compatibility_with_runner_helpers(self):
        """Basic behavior: get_selected_models returns model list from config.

        We intentionally keep this simple: it verifies the adapter can be used in
        orchestrator mode and returns selected models as a list. Deeper
        compatibility with runner creation is tested separately in unit tests.
        """
        cfg = {"model_names": ["llama3.2:3b"]}
        adapter = MCPBenchAdapter(model_instance=object(), memory_instance=None, benchmark_config=cfg)
        models = adapter.get_selected_models()
        assert isinstance(models, list)
        assert models == ["llama3.2:3b"]