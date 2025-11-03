"""
Tests for MCPBench benchmark adapter.

This module tests the adapter that integrates MCP Benchmark runner
with the config-driven evaluation system.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime


@pytest.fixture
def sample_config():
    """Sample configuration for MCP Bench testing."""
    return {
        "model": "ollama",
        "model_name": "llama3.1:8b",
        "tasks_file": "datasets/mcp_bench/tasks/tasks.json",
        "temperature": 0.3,
        "max_tokens": 1000,
        "task_limit": 5,
        "enable_distraction_servers": False,
        "distraction_count": 0,
        "enable_judge_stability": True,
        "filter_problematic_tools": True,
        "save_directory": "results/mcpbench",
    }


@pytest.fixture
def sample_task():
    """Sample task data structure."""
    return {
        "task_id": "test_task_1",
        "description": "Test task description",
        "server_name": "test_server",
        "expected_output": {"result": "success"},
        "ground_truth": "expected result"
    }


@pytest.fixture
def sample_execution_result():
    """Sample execution result from benchmark runner."""
    return {
        "success": True,
        "output": "Task completed successfully",
        "tool_calls": [
            {"name": "test_tool", "arguments": {"param": "value"}}
        ],
        "metrics": {
            "token_usage": 150,
            "time_taken": 2.5,
            "turn_count": 3
        }
    }


@pytest.fixture
def sample_evaluation_result():
    """Sample evaluation result from TaskEvaluator."""
    return {
        "overall_score": 0.85,
        "schema_understanding": 0.9,
        "task_completion": 0.8,
        "tool_usage": 0.85,
        "planning_effectiveness": 0.85,
        "details": {
            "correct_tools_used": True,
            "task_completed": True,
            "reasoning": "Task completed successfully with correct tools"
        }
    }


class TestMCPBenchAdapterInitialization:
    """Test adapter initialization and configuration."""
    
    def test_adapter_creation_with_valid_config(self, sample_config):
        """Test creating adapter with valid configuration."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        adapter = MCPBenchAdapter(sample_config)
        
        assert adapter.config == sample_config
        assert adapter.model_name == "llama3.1:8b"
        assert adapter.model_provider == "ollama"
        assert adapter.tasks_file == "datasets/mcp_bench/tasks/tasks.json"
        assert adapter.task_limit == 5
    
    def test_adapter_creation_with_missing_required_fields(self):
        """Test adapter raises error when required config fields are missing."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        incomplete_config = {
            "model": "ollama",
            # missing model_name
        }
        
        with pytest.raises(ValueError, match="Missing required config field"):
            MCPBenchAdapter(incomplete_config)
    
    def test_adapter_uses_default_values_for_optional_fields(self):
        """Test adapter applies default values for optional configuration."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        minimal_config = {
            "model": "ollama",
            "model_name": "llama3.1:8b",
            "tasks_file": "tasks.json"
        }
        
        adapter = MCPBenchAdapter(minimal_config)
        
        assert adapter.temperature == 0.3  # default
        assert adapter.max_tokens == 1000  # default
        assert adapter.task_limit is None  # default
        assert adapter.enable_distraction_servers is False  # default
    
    def test_adapter_validates_task_file_path(self, sample_config):
        """Test adapter validates tasks file path format."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        sample_config["tasks_file"] = ""
        
        with pytest.raises(ValueError, match="tasks_file cannot be empty"):
            MCPBenchAdapter(sample_config)


class TestMCPBenchAdapterBenchmarkExecution:
    """Test benchmark execution through the adapter."""
    
    @pytest.mark.asyncio
    async def test_run_benchmark_initializes_runner_correctly(self, sample_config):
        """Test that run_benchmark properly initializes BenchmarkRunner."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        adapter = MCPBenchAdapter(sample_config)
        
        with patch('evaluation.mcpbench_adapter.BenchmarkRunner') as mock_runner_class:
            mock_runner = AsyncMock()
            mock_runner.run_benchmark = AsyncMock(return_value={"results": []})
            mock_runner_class.return_value = mock_runner
            
            await adapter.run_benchmark()
            
            # Verify runner was created with correct parameters
            mock_runner_class.assert_called_once()
            call_kwargs = mock_runner_class.call_args[1]
            assert call_kwargs["tasks_file"] == sample_config["tasks_file"]
            assert not call_kwargs["enable_distraction_servers"]
            assert call_kwargs["filter_problematic_tools"]
    
    @pytest.mark.asyncio
    async def test_run_benchmark_returns_formatted_results(self, sample_config, sample_execution_result):
        """Test that run_benchmark returns properly formatted results."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        adapter = MCPBenchAdapter(sample_config)
        
        mock_results = {
            "models": {
                "llama3.1:8b": {
                    "tasks": [sample_execution_result],
                    "overall_score": 0.85
                }
            },
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_tasks": 1
            }
        }
        
        with patch('evaluation.mcpbench_adapter.BenchmarkRunner') as mock_runner_class:
            mock_runner = AsyncMock()
            mock_runner.run_benchmark = AsyncMock(return_value=mock_results)
            mock_runner_class.return_value = mock_runner
            
            results = await adapter.run_benchmark()
            
            assert "models" in results
            assert "llama3.1:8b" in results["models"]
            assert results["models"]["llama3.1:8b"]["overall_score"] == 0.85
    
    @pytest.mark.asyncio
    async def test_run_benchmark_handles_task_limit(self, sample_config):
        """Test that task_limit is properly passed to runner."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        sample_config["task_limit"] = 10
        adapter = MCPBenchAdapter(sample_config)
        
        with patch('evaluation.mcpbench_adapter.BenchmarkRunner') as mock_runner_class:
            mock_runner = AsyncMock()
            mock_runner.run_benchmark = AsyncMock(return_value={"results": []})
            mock_runner_class.return_value = mock_runner
            
            await adapter.run_benchmark()
            
            # Verify task_limit was passed
            mock_runner.run_benchmark.assert_called_once()
            call_kwargs = mock_runner.run_benchmark.call_args[1]
            assert call_kwargs.get("task_limit") == 10
    
    @pytest.mark.asyncio
    async def test_run_benchmark_handles_execution_errors(self, sample_config):
        """Test that run_benchmark handles execution errors gracefully."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        adapter = MCPBenchAdapter(sample_config)
        
        with patch('evaluation.mcpbench_adapter.BenchmarkRunner') as mock_runner_class:
            mock_runner = AsyncMock()
            mock_runner.run_benchmark = AsyncMock(side_effect=Exception("Execution failed"))
            mock_runner_class.return_value = mock_runner
            
            with pytest.raises(Exception, match="Execution failed"):
                await adapter.run_benchmark()


class TestMCPBenchAdapterEvaluation:
    """Test evaluation methods of the adapter."""
    
    def test_evaluate_result_with_successful_task(self, sample_task, sample_execution_result, sample_evaluation_result):
        """Test evaluation of a successful task result."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        adapter = MCPBenchAdapter({
            "model": "ollama",
            "model_name": "test",
            "tasks_file": "test.json"
        })
        
        with patch('evaluation.mcpbench_adapter.TaskEvaluator') as mock_evaluator_class:
            mock_evaluator = Mock()
            mock_evaluator.evaluate_task = Mock(return_value=sample_evaluation_result)
            mock_evaluator_class.return_value = mock_evaluator
            
            result = adapter.evaluate_result(sample_task, sample_execution_result)
            
            assert result["success"]
            assert result["overall_score"] == 0.85
            assert "schema_understanding" in result
    
    def test_evaluate_result_with_failed_task(self, sample_task):
        """Test evaluation of a failed task result."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        adapter = MCPBenchAdapter({
            "model": "ollama",
            "model_name": "test",
            "tasks_file": "test.json"
        })
        
        failed_result = {
            "success": False,
            "error": "Task execution failed",
            "metrics": {}
        }
        
        eval_result = {
            "overall_score": 0.0,
            "schema_understanding": 0.0,
            "task_completion": 0.0,
            "tool_usage": 0.0,
            "planning_effectiveness": 0.0,
        }
        
        with patch('evaluation.mcpbench_adapter.TaskEvaluator') as mock_evaluator_class:
            mock_evaluator = Mock()
            mock_evaluator.evaluate_task = Mock(return_value=eval_result)
            mock_evaluator_class.return_value = mock_evaluator
            
            result = adapter.evaluate_result(sample_task, failed_result)
            
            assert not result["success"]
            assert result["overall_score"] == 0.0
    
    def test_evaluate_result_validates_input(self):
        """Test that evaluate_result validates input parameters."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        adapter = MCPBenchAdapter({
            "model": "ollama",
            "model_name": "test",
            "tasks_file": "test.json"
        })
        
        with pytest.raises(ValueError, match="task cannot be None"):
            adapter.evaluate_result(None, {})
        
        with pytest.raises(ValueError, match="execution_result cannot be None"):
            adapter.evaluate_result({}, None)


class TestMCPBenchAdapterConfigLoading:
    """Test configuration loading from TOML files."""
    
    def test_load_config_from_toml_file(self, tmp_path):
        """Test loading configuration from a TOML file."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        config_content = """
[mcpbench]
model = "ollama"
model_name = "llama3.1:8b"
tasks_file = "datasets/mcp_bench/tasks/tasks.json"
temperature = 0.5
max_tokens = 2000
task_limit = 10
        """
        
        config_file = tmp_path / "test_config.toml"
        config_file.write_text(config_content)
        
        config = MCPBenchAdapter.load_config_from_file(str(config_file), section="mcpbench")
        
        assert config["model"] == "ollama"
        assert config["model_name"] == "llama3.1:8b"
        assert config["temperature"] == 0.5
        assert config["task_limit"] == 10
    
    def test_load_config_handles_missing_file(self):
        """Test error handling when config file doesn't exist."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        with pytest.raises(FileNotFoundError):
            MCPBenchAdapter.load_config_from_file("nonexistent.toml")
    
    def test_load_config_handles_missing_section(self, tmp_path):
        """Test error handling when config section doesn't exist."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        config_content = """
[nestful]
model = "test"
        """
        
        config_file = tmp_path / "test_config.toml"
        config_file.write_text(config_content)
        
        with pytest.raises(ValueError, match="Section 'mcpbench' not found"):
            MCPBenchAdapter.load_config_from_file(str(config_file), section="mcpbench")
    
    def test_load_config_handles_invalid_toml(self, tmp_path):
        """Test error handling for malformed TOML files."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        config_file = tmp_path / "invalid.toml"
        config_file.write_text("this is not [ valid toml")
        
        with pytest.raises(Exception):  # TOML parsing error
            MCPBenchAdapter.load_config_from_file(str(config_file))


class TestMCPBenchAdapterResultsSaving:
    """Test results saving functionality."""
    
    @pytest.mark.asyncio
    async def test_save_results_creates_output_directory(self, sample_config, tmp_path):
        """Test that save_results creates output directory if it doesn't exist."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        output_dir = tmp_path / "test_results"
        sample_config["save_directory"] = str(output_dir)
        
        adapter = MCPBenchAdapter(sample_config)
        results = {"test": "data"}
        
        output_file = await adapter.save_results(results)
        
        assert output_dir.exists()
        assert Path(output_file).exists()
    
    @pytest.mark.asyncio
    async def test_save_results_generates_timestamped_filename(self, sample_config, tmp_path):
        """Test that save_results generates timestamped filenames."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        sample_config["save_directory"] = str(tmp_path)
        adapter = MCPBenchAdapter(sample_config)
        results = {"test": "data"}
        
        output_file = await adapter.save_results(results)
        
        filename = Path(output_file).name
        assert filename.startswith("mcpbench_results_")
        assert filename.endswith(".json")
    
    @pytest.mark.asyncio
    async def test_save_results_with_custom_filename(self, sample_config, tmp_path):
        """Test saving results with a custom filename."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        sample_config["save_directory"] = str(tmp_path)
        adapter = MCPBenchAdapter(sample_config)
        results = {"test": "data"}
        
        custom_name = "custom_results.json"
        output_file = await adapter.save_results(results, filename=custom_name)
        
        assert Path(output_file).name == custom_name
    
    @pytest.mark.asyncio
    async def test_save_results_preserves_json_structure(self, sample_config, tmp_path):
        """Test that saved results maintain correct JSON structure."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        import json
        
        sample_config["save_directory"] = str(tmp_path)
        adapter = MCPBenchAdapter(sample_config)
        
        results = {
            "models": {
                "test_model": {
                    "score": 0.85,
                    "tasks": [{"id": 1, "success": True}]
                }
            },
            "metadata": {"timestamp": "2024-01-01"}
        }
        
        output_file = await adapter.save_results(results)
        
        with open(output_file, 'r') as f:
            loaded_results = json.load(f)
        
        assert loaded_results == results


class TestMCPBenchAdapterModelSelection:
    """Test model selection and configuration."""
    
    def test_adapter_supports_single_model(self, sample_config):
        """Test adapter with single model configuration."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        adapter = MCPBenchAdapter(sample_config)
        models = adapter.get_selected_models()
        
        assert len(models) == 1
        assert models[0] == "llama3.1:8b"
    
    def test_adapter_supports_multiple_models(self):
        """Test adapter with multiple models configuration."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        config = {
            "model": "ollama",
            "model_names": ["llama3.1:8b", "mistral:7b", "phi3:mini"],
            "tasks_file": "test.json"
        }
        
        adapter = MCPBenchAdapter(config)
        models = adapter.get_selected_models()
        
        assert len(models) == 3
        assert "llama3.1:8b" in models
        assert "mistral:7b" in models
    
    def test_adapter_validates_model_provider(self):
        """Test that adapter validates model provider."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        config = {
            "model": "invalid_provider",
            "model_name": "test",
            "tasks_file": "test.json"
        }
        
        adapter = MCPBenchAdapter(config)
        
        with pytest.raises(ValueError, match="Unsupported model provider"):
            adapter._validate_model_provider()


class TestMCPBenchAdapterIntegration:
    """Integration tests for the complete adapter workflow."""
    
    @pytest.mark.asyncio
    async def test_full_benchmark_workflow(self, sample_config, tmp_path):
        """Test complete workflow from config to results."""
        from evaluation.mcpbench_adapter import MCPBenchAdapter
        
        sample_config["save_directory"] = str(tmp_path)
        adapter = MCPBenchAdapter(sample_config)
        
        mock_results = {
            "models": {
                "llama3.1:8b": {
                    "tasks": [{"id": 1, "success": True, "score": 0.85}],
                    "overall_score": 0.85
                }
            }
        }
        
        with patch('evaluation.mcpbench_adapter.BenchmarkRunner') as mock_runner_class:
            mock_runner = AsyncMock()
            mock_runner.run_benchmark = AsyncMock(return_value=mock_results)
            mock_runner_class.return_value = mock_runner
            
            results = await adapter.run_benchmark()
            output_file = await adapter.save_results(results)
            
            assert Path(output_file).exists()
            assert results["models"]["llama3.1:8b"]["overall_score"] == 0.85
