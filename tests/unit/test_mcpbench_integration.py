"""
Integration test for the config-driven MCPBenchAdapter functionality.

This test verifies that the new config-driven approach works with the 
actual benchmark runner components.
"""
import tempfile
import os
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from evaluation.mcpbench_adapter import MCPBenchAdapter


class TestMCPBenchAdapterIntegration:
    """Integration tests for the config-driven MCPBenchAdapter."""

    def test_parse_arguments_from_config_integration(self):
        """Test that parse_arguments_from_config produces valid args for runner."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("""
model_names = ["llama3.2:3b"]

[mcpbench]
provider = "ollama"
tasks_file = "datasets/mcp_bench/tasks/mcpbench_tasks_single_runner_format.json"
temperature = 0.3
max_tokens = 1000
task_limit = 2
enable_distraction_servers = false
distraction_count = 0
enable_judge_stability = true
filter_problematic_tools = true
concurrent_summarization = true
use_fuzzy_descriptions = false
verbose = false
output = "test_results.json"
enable_cache = false
cache_ttl = 24
cache_dir = "./cache"
""")
            config_path = f.name

        try:
            adapter = MCPBenchAdapter(config_path)
            args = adapter.parse_arguments_from_config()
            
            # Validate args structure matches what runner functions expect
            assert hasattr(args, 'models')
            assert hasattr(args, 'tasks_file') 
            assert hasattr(args, 'verbose')
            assert hasattr(args, 'distraction_count')
            assert hasattr(args, 'disable_judge_stability')
            assert hasattr(args, 'disable_filter_problematic_tools')
            assert hasattr(args, 'disable_concurrent_summarization')
            assert hasattr(args, 'disable_fuzzy')
            assert hasattr(args, 'output')
            assert hasattr(args, 'enable_cache')
            assert hasattr(args, 'cache_ttl')
            assert hasattr(args, 'cache_dir')
            
            # Validate specific values
            assert args.models == ["llama3.2:3b"]
            assert args.tasks_file == "datasets/mcp_bench/tasks/mcpbench_tasks_single_runner_format.json"
            assert not args.verbose
            assert args.distraction_count == 0
            assert not args.disable_judge_stability  # inverted from enable_judge_stability=true
            assert not args.disable_filter_problematic_tools  # inverted from filter_problematic_tools=true
            assert not args.disable_concurrent_summarization  # inverted
            assert args.disable_fuzzy  # inverted from use_fuzzy_descriptions=false
            assert args.output == "test_results.json"
            assert not args.enable_cache
            assert args.cache_ttl == 24
            assert args.cache_dir == "./cache"
            
        finally:
            os.unlink(config_path)

    def test_parse_and_validate_args_from_config_integration(self):
        """Test that parse_and_validate_args_from_config works with existing task files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("""
model_names = ["llama3.2:3b"]

[mcpbench]
provider = "ollama"
tasks_file = "datasets/mcp_bench/tasks/mcpbench_tasks_single_runner_format.json"
distraction_count = 0
verbose = false
""")
            config_path = f.name

        try:
            adapter = MCPBenchAdapter(config_path)
            args, tasks_file, enable_distraction = adapter.parse_and_validate_args_from_config()
            
            # Validate return values match expected format
            assert hasattr(args, 'verbose')
            assert hasattr(args, 'distraction_count') 
            assert isinstance(tasks_file, str)
            assert isinstance(enable_distraction, bool)
            
            # Validate specific values
            assert not args.verbose
            assert args.distraction_count == 0
            assert tasks_file == "datasets/mcp_bench/tasks/mcpbench_tasks_single_runner_format.json"
            assert not enable_distraction  # because distraction_count == 0
            
        finally:
            os.unlink(config_path)

    def test_config_driven_approach_matches_runner_expectations(self):
        """Test that config-driven args can be used with runner helper functions."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("""
model_names = ["llama3.2:3b"]

[mcpbench]
provider = "ollama"
tasks_file = "tasks/mcpbench_tasks_single_runner_format.json"
temperature = 0.3
max_tokens = 1000
task_limit = 2
enable_distraction_servers = false
distraction_count = 0
enable_judge_stability = true
filter_problematic_tools = true
concurrent_summarization = true
use_fuzzy_descriptions = false
verbose = false
""")
            config_path = f.name

        try:
            adapter = MCPBenchAdapter(config_path)
            args, tasks_file, enable_distraction = adapter.parse_and_validate_args_from_config()
            
            # Import runner helper functions to test compatibility
            from datasets.mcp_bench.benchmark.runner import (
                _create_runner_and_get_models,
                _determine_selected_models
            )
            
            # Test that the args work with actual runner functions
            # This validates that our config-driven args have the right structure
            runner, selected_models = _create_runner_and_get_models(
                args, tasks_file, enable_distraction
            )
            
            # Should successfully create runner
            assert runner is not None
            assert isinstance(selected_models, list)
            
            # Test model selection
            final_models = _determine_selected_models(args, selected_models)
            assert isinstance(final_models, list)
            
        finally:
            os.unlink(config_path)