"""
Tests for MCPBenchAdapter config-driven argument parsing.

This module tests the config-driven replacement of parse_arguments() 
and _parse_and_validate_args() functions in MCPBenchAdapter.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from types import SimpleNamespace

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from evaluation.mcpbench_adapter import MCPBenchAdapter


class TestMCPBenchAdapterConfigParsing:
    """Test config-driven argument parsing in MCPBenchAdapter."""

    def test_config_driven_parse_arguments_basic(self):
        """Test that parse_arguments_from_config reads basic parameters from config."""
        # This test should fail initially as the method doesn't exist yet
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("""
model_names = ["llama3.2:3b"]

[mcpbench]
provider = "ollama"
tasks_file = "test_tasks.json"
temperature = 0.3
max_tokens = 1000
task_limit = 5
enable_distraction_servers = false
distraction_count = 0
enable_judge_stability = true
filter_problematic_tools = true
concurrent_summarization = true
use_fuzzy_descriptions = false
verbose = false
output = "test_output.json"
enable_cache = true
cache_ttl = 24
cache_dir = "test_cache"
""")
            config_path = f.name

        try:
            adapter = MCPBenchAdapter(config_path)
            # This method doesn't exist yet - will fail
            args = adapter.parse_arguments_from_config()
            
            # Expected behavior after implementation
            assert args.models == ["llama3.2:3b"]
            assert args.tasks_file == "test_tasks.json"
            assert not args.verbose
            assert args.distraction_count == 0
            assert not args.disable_judge_stability  # inverted from enable_judge_stability
            assert not args.disable_filter_problematic_tools  # inverted
            assert not args.disable_concurrent_summarization  # inverted
            assert args.disable_fuzzy  # inverted from use_fuzzy_descriptions
            assert args.output == "test_output.json"
            assert args.enable_cache
            assert args.cache_ttl == 24
            assert args.cache_dir == "test_cache"
            
        finally:
            os.unlink(config_path)

    def test_config_driven_parse_arguments_defaults(self):
        """Test that parse_arguments_from_config applies correct defaults."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("""
model_names = ["test_model"]

[mcpbench]
provider = "ollama"
""")
            config_path = f.name

        try:
            adapter = MCPBenchAdapter(config_path)
            # This method doesn't exist yet - will fail
            args = adapter.parse_arguments_from_config()
            
            # Expected defaults after implementation
            assert args.models == ["test_model"] 
            assert not args.list_models
            assert not args.verbose
            assert args.distraction_count == 10  # default from benchmark config
            assert not args.disable_judge_stability  # default enabled
            assert not args.disable_filter_problematic_tools  # default enabled
            assert not args.disable_concurrent_summarization  # default enabled  
            assert args.disable_fuzzy  # default use_fuzzy_descriptions False
            assert not args.enable_cache  # default
            assert args.cache_ttl == 0  # default
            assert args.cache_dir == "./cache"  # default
            
        finally:
            os.unlink(config_path)

    def test_config_driven_parse_and_validate_args(self):
        """Test config-driven replacement of _parse_and_validate_args."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("""
model_names = ["test_model"]

[mcpbench]
tasks_file = "datasets/mcp_bench/tasks/mcpbench_tasks_single_runner_format.json"
distraction_count = 5
verbose = true
""")
            config_path = f.name

        try:
            adapter = MCPBenchAdapter(config_path)
            # This method doesn't exist yet - will fail
            args, tasks_file, enable_distraction = adapter.parse_and_validate_args_from_config()
            
            # Expected behavior after implementation
            assert hasattr(args, 'verbose') and args.verbose
            assert hasattr(args, 'distraction_count') and args.distraction_count == 5
            assert tasks_file == "datasets/mcp_bench/tasks/mcpbench_tasks_single_runner_format.json"
            assert enable_distraction  # because distraction_count > 0
            
        finally:
            os.unlink(config_path)

    def test_config_driven_parse_and_validate_args_no_distraction(self):
        """Test that enable_distraction is False when distraction_count is 0."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("""
model_names = ["test_model"]

[mcpbench]
tasks_file = "datasets/mcp_bench/tasks/mcpbench_tasks_single_runner_format.json"
distraction_count = 0
""")
            config_path = f.name

        try:
            adapter = MCPBenchAdapter(config_path)
            # This method doesn't exist yet - will fail
            args, tasks_file, enable_distraction = adapter.parse_and_validate_args_from_config()
            
            assert not enable_distraction  # because distraction_count == 0
            
        finally:
            os.unlink(config_path)

    def test_config_file_validation(self):
        """Test that file paths are validated when specified."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("""
model_names = ["test_model"]

[mcpbench]
tasks_file = "nonexistent_file.json"
""")
            config_path = f.name

        try:
            adapter = MCPBenchAdapter(config_path)
            # This should fail when the method validates file existence
            with pytest.raises((FileNotFoundError, ValueError)):
                adapter.parse_and_validate_args_from_config()
                
        finally:
            os.unlink(config_path)

    def test_multiple_tasks_files_validation(self):
        """Test validation of comma-separated task files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("""
model_names = ["test_model"]

[mcpbench]
tasks_file = "file1.json,file2.json"
""")
            config_path = f.name

        try:
            adapter = MCPBenchAdapter(config_path)
            # This should fail when the method validates file existence
            with pytest.raises((FileNotFoundError, ValueError)):
                adapter.parse_and_validate_args_from_config()
                
        finally:
            os.unlink(config_path)

    def test_config_parameter_mapping(self):
        """Test that config parameters map correctly to argument namespace."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("""
model_names = ["model1", "model2"]

[mcpbench]
provider = "ollama"
tasks_file = "tasks.json"
temperature = 0.5
max_tokens = 2000
task_limit = 10
enable_distraction_servers = true
distraction_count = 3
enable_judge_stability = false
filter_problematic_tools = false
concurrent_summarization = false
use_fuzzy_descriptions = true
verbose = true
output = "custom_output.json"
enable_cache = false
cache_ttl = 48
cache_dir = "custom_cache"
""")
            config_path = f.name

        try:
            adapter = MCPBenchAdapter(config_path)
            # This method doesn't exist yet - will fail
            args = adapter.parse_arguments_from_config()
            
            # Test all parameter mappings
            assert args.models == ["model1", "model2"]
            assert args.tasks_file == "tasks.json"
            assert args.verbose
            assert args.distraction_count == 3
            assert args.disable_judge_stability  # inverted from enable_judge_stability=false
            assert args.disable_filter_problematic_tools  # inverted 
            assert args.disable_concurrent_summarization  # inverted
            assert not args.disable_fuzzy  # inverted from use_fuzzy_descriptions=true
            assert args.output == "custom_output.json"
            assert not args.enable_cache
            assert args.cache_ttl == 48
            assert args.cache_dir == "custom_cache"
            
        finally:
            os.unlink(config_path)