"""
Simplified tests for MCPBenchAdapter config file-based initialization.

This module tests only the config.toml file-based configuration approach.
"""
import pytest
import tempfile
import os
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from evaluation.mcp_bench.mcpbench_adapter import MCPBenchAdapter


class TestMCPBenchAdapterConfigFile:
    """Test config file-based initialization of MCPBenchAdapter."""

    def test_adapter_creation_with_valid_config_file(self):
        """Test creating adapter with valid config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("""
model_names = ["llama3.2:3b"]

[datasets.mcpbench]
provider = "ollama"
tasks_file = "datasets/mcp_bench/tasks/mcpbench_tasks_single_runner_format.json"
temperature = 0.3
max_tokens = 1000
task_limit = 5
enable_distraction_servers = false
distraction_count = 0
enable_judge_stability = true
filter_problematic_tools = true
concurrent_summarization = true
use_fuzzy_descriptions = false
results_dir = "results/mcpbench"
""")
            config_path = f.name

        try:
            adapter = MCPBenchAdapter(config_path)
            
            # Validate that config was loaded correctly
            assert "model_names" in adapter.cfg
            assert adapter.cfg["model_names"] == ["llama3.2:3b"]
            assert adapter.cfg["provider"] == "ollama"
            assert adapter.cfg["task_limit"] == 5
            assert adapter.cfg["enable_judge_stability"]
            assert adapter.cfg["filter_problematic_tools"]
            
        finally:
            os.unlink(config_path)

    def test_adapter_creation_with_default_config(self):
        """Test creating adapter with default config path."""
        # This should use evaluation/config.toml by default
        adapter = MCPBenchAdapter()
        
        # Should have loaded config successfully
        assert hasattr(adapter, 'cfg')
        assert isinstance(adapter.cfg, dict)

    def test_adapter_creation_with_missing_config_file(self):
        """Test that adapter raises error when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            MCPBenchAdapter("nonexistent_config.toml")

    def test_adapter_creation_with_missing_mcpbench_section(self):
        """Test that adapter raises error when mcpbench section is missing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("""
model_names = ["test_model"]

[nestful]
provider = "ollama"
""")
            config_path = f.name

        try:
            with pytest.raises(ValueError, match="Section 'mcpbench' not found"):
                MCPBenchAdapter(config_path)
                
        finally:
            os.unlink(config_path)

    def test_parse_arguments_from_config_method_exists(self):
        """Test that the new parse_arguments_from_config method exists."""
        adapter = MCPBenchAdapter()
        
        # Method should exist and be callable
        assert hasattr(adapter, 'parse_arguments_from_config')
        assert callable(adapter.parse_arguments_from_config)

    def test_parse_and_validate_args_from_config_method_exists(self):
        """Test that the new parse_and_validate_args_from_config method exists."""
        adapter = MCPBenchAdapter()
        
        # Method should exist and be callable
        assert hasattr(adapter, 'parse_and_validate_args_from_config')
        assert callable(adapter.parse_and_validate_args_from_config)

    def test_get_selected_models_method_works(self):
        """Test that get_selected_models works with config file."""
        adapter = MCPBenchAdapter()
        
        # Should be able to get models from config
        models = adapter.get_selected_models()
        assert isinstance(models, list)
        assert len(models) > 0