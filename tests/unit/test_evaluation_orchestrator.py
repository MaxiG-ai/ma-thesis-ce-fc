"""
Tests for the EvaluationOrchestrator class.
"""

import sys
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_evaluation_orchestrator_initialization():
    """Test EvaluationOrchestrator initialization."""
    from evaluation.orchestrator import EvaluationOrchestrator
    
    config = {
        "providers": {
            "ollama": {
                "models": ["llama3.2:3b"],
                "enabled_models": ["llama3.2:3b"],
                "temperature": 0.3,
                "max_tokens": 1000
            }
        },
        "memory_methods": ["truncation"],
        "executed_benchmarks": ["nestful"],
        "benchmarks": {
            "nestful": {
                "dataset": "data_v2/nestful_data.jsonl",
                "temperature": 0.0,
                "max_tokens": 1000
            }
        }
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        orchestrator = EvaluationOrchestrator(config, results_dir=temp_dir)
        
        assert orchestrator.config == config
        assert orchestrator.results_storage is not None
        assert len(orchestrator.model_specs) == 1
        assert orchestrator.model_specs[0]["name"] == "llama3.2:3b"
        assert orchestrator.model_specs[0]["provider"] == "ollama"


def test_evaluation_orchestrator_parse_model_specs():
    """Test parsing model specifications from config."""
    from evaluation.orchestrator import EvaluationOrchestrator
    
    config = {
        "providers": {
            "ollama": {
                "models": ["llama3.2:3b", "llama3.1:8b"],
                "enabled_models": ["llama3.2:3b", "llama3.1:8b"],
                "temperature": 0.3
            }
        },
        "memory_methods": ["truncation"],
        "executed_benchmarks": ["nestful"]
    }
    
    orchestrator = EvaluationOrchestrator(config)
    model_specs = orchestrator.model_specs
    
    assert len(model_specs) == 2
    assert model_specs[0]["name"] == "llama3.2:3b"
    assert model_specs[0]["provider"] == "ollama"
    assert model_specs[1]["name"] == "llama3.1:8b"
    assert model_specs[1]["provider"] == "ollama"


def test_evaluation_orchestrator_generate_combinations():
    """Test generating all evaluation combinations."""
    from evaluation.orchestrator import EvaluationOrchestrator
    
    config = {
        "providers": {
            "ollama": {
                "models": ["llama3.2:3b", "llama3.1:8b"],
                "enabled_models": ["llama3.2:3b", "llama3.1:8b"],
                "temperature": 0.3
            }
        },
        "memory_methods": ["truncation"],
        "executed_benchmarks": ["nestful", "mcpbench"]
    }
    
    orchestrator = EvaluationOrchestrator(config)
    combinations = list(orchestrator._generate_combinations())
    
    # Should have 2 models × 1 memory × 2 benchmarks = 4 combinations
    assert len(combinations) == 4
    
    # Check first combination
    model_spec, memory_method, benchmark = combinations[0]
    assert model_spec["name"] in ["llama3.2:3b", "llama3.1:8b"]
    assert memory_method == "truncation"
    assert benchmark in ["nestful", "mcpbench"]


@patch('evaluation.orchestrator.ComponentRegistry')
async def test_evaluation_orchestrator_run_single_evaluation(mock_registry):
    """Test running a single evaluation combination."""
    from evaluation.orchestrator import EvaluationOrchestrator
    
    # Mock components
    mock_model = AsyncMock()
    mock_model.generate_text.return_value = {"message": {"content": "test response"}}
    mock_model.get_model_info.return_value = {"model": "test", "provider": "test"}
    
    mock_memory = MagicMock()
    mock_memory.process.return_value = "processed text"
    
    mock_benchmark = AsyncMock()
    mock_benchmark.run_benchmark.return_value = {
        "score": 0.85,
        "tasks": 10,
        "successful": 8
    }
    
    mock_registry.return_value.create_model.return_value = mock_model
    mock_registry.return_value.create_memory_method.return_value = mock_memory
    mock_registry.return_value.create_benchmark.return_value = mock_benchmark
    
    config = {
        "providers": {
            "test": {
                "models": ["test-model"],
                "enabled_models": ["test-model"],
                "temperature": 0.3
            }
        },
        "memory_methods": ["truncation"],
        "executed_benchmarks": ["test-benchmark"],
        "benchmarks": {
            "test-benchmark": {
                "temperature": 0.0,
                "max_tokens": 1000
            }
        }
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        orchestrator = EvaluationOrchestrator(config, results_dir=temp_dir)
        
        model_spec = {"name": "test-model", "provider": "test"}
        result = await orchestrator._run_single_evaluation(
            model_spec, "truncation", "test-benchmark"
        )
        
        assert result["status"] == "success"
        assert result["model"] == model_spec
        assert result["memory_method"] == "truncation"
        assert result["benchmark"] == "test-benchmark"
        assert "duration_seconds" in result
        assert "results" in result


@patch('evaluation.orchestrator.ComponentRegistry')
async def test_evaluation_orchestrator_run_single_evaluation_error(mock_registry):
    """Test error handling in single evaluation."""
    from evaluation.orchestrator import EvaluationOrchestrator
    
    # Mock components that raise errors
    mock_registry.return_value.create_model.side_effect = Exception("Model creation failed")
    
    config = {
        "providers": {
            "test": {
                "models": ["test-model"],
                "enabled_models": ["test-model"],
                "temperature": 0.3
            }
        },
        "memory_methods": ["truncation"],
        "executed_benchmarks": ["test-benchmark"],
        "benchmarks": {
            "test-benchmark": {
                "temperature": 0.0,
                "max_tokens": 1000
            }
        }
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        orchestrator = EvaluationOrchestrator(config, results_dir=temp_dir)
        
        model_spec = {"name": "test-model", "provider": "test"}
        result = await orchestrator._run_single_evaluation_with_error_handling(
            model_spec, "truncation", "test-benchmark"
        )
        
        assert result["status"] == "error"
        assert "Model creation failed" in str(result["error"])


@patch('evaluation.orchestrator.ComponentRegistry')
async def test_evaluation_orchestrator_run_full_evaluation(mock_registry):
    """Test running full evaluation with all combinations."""
    from evaluation.orchestrator import EvaluationOrchestrator
    
    # Mock successful components
    mock_model = AsyncMock()
    mock_model.generate_text.return_value = {"message": {"content": "test"}}
    mock_model.get_model_info.return_value = {"model": "test", "provider": "test"}
    
    mock_memory = MagicMock()
    mock_memory.process.return_value = "processed"
    
    mock_benchmark = AsyncMock()
    mock_benchmark.run_benchmark.return_value = {"score": 0.85}
    
    mock_registry.return_value.create_model.return_value = mock_model
    mock_registry.return_value.create_memory_method.return_value = mock_memory
    mock_registry.return_value.create_benchmark.return_value = mock_benchmark
    
    config = {
        "providers": {
            "test": {
                "models": ["model1", "model2"],
                "enabled_models": ["model1", "model2"],
                "temperature": 0.3
            }
        },
        "memory_methods": ["truncation"],
        "executed_benchmarks": ["benchmark1"],
        "benchmarks": {
            "benchmark1": {
                "temperature": 0.0,
                "max_tokens": 1000
            }
        }
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        orchestrator = EvaluationOrchestrator(config, results_dir=temp_dir)
        
        summary = await orchestrator.run_full_evaluation()
        
        assert summary["total_runs"] == 2  # 2 models × 1 memory × 1 benchmark
        assert summary["successful_runs"] == 2
        assert summary["failed_runs"] == 0
        assert summary["success_rate"] == 1.0


def test_evaluation_orchestrator_create_error_result():
    """Test creating error result entries."""
    from evaluation.orchestrator import EvaluationOrchestrator
    
    config = {
        "providers": {
            "test": {
                "models": ["test"],
                "enabled_models": ["test"],
                "temperature": 0.3
            }
        },
        "memory_methods": ["truncation"],
        "executed_benchmarks": ["test-benchmark"]
    }
    
    orchestrator = EvaluationOrchestrator(config)
    
    model_spec = {"name": "test-model", "provider": "test"}
    error_result = orchestrator._create_error_result(
        model_spec, "truncation", "benchmark", "Test error message"
    )
    
    assert error_result["status"] == "error"
    assert error_result["model"] == model_spec
    assert error_result["memory_method"] == "truncation"
    assert error_result["benchmark"] == "benchmark"
    assert error_result["error"] == "Test error message"
    assert "timestamp" in error_result


def test_evaluation_orchestrator_generate_summary():
    """Test summary generation from results."""
    from evaluation.orchestrator import EvaluationOrchestrator
    
    config = {
        "providers": {
            "test": {
                "models": ["test"],
                "enabled_models": ["test"],
                "temperature": 0.3
            }
        },
        "memory_methods": ["truncation"],
        "executed_benchmarks": ["test-benchmark"]
    }
    
    orchestrator = EvaluationOrchestrator(config)
    
    results = [
        {"status": "success", "model": {"name": "model1"}, "memory_method": "truncation", "benchmark": "test1"},
        {"status": "success", "model": {"name": "model2"}, "memory_method": "truncation", "benchmark": "test2"},
        {"status": "error", "model": {"name": "model3"}, "memory_method": "truncation", "benchmark": "test3"}
    ]
    
    summary = orchestrator._generate_summary(results)
    
    assert summary["total_runs"] == 3
    assert summary["successful_runs"] == 2
    assert summary["failed_runs"] == 1
    assert summary["success_rate"] == 2/3
    assert len(summary["results"]) == 3
    assert "models_tested" in summary
    assert "memory_methods_tested" in summary
    assert "benchmarks_tested" in summary


@patch('evaluation.orchestrator.ComponentRegistry')
async def test_evaluation_orchestrator_with_concurrent_evaluations(mock_registry):
    """Test orchestrator with concurrent evaluation setting."""
    from evaluation.orchestrator import EvaluationOrchestrator
    
    # Mock components with delays
    mock_model = AsyncMock()
    mock_model.generate_text.return_value = {"message": {"content": "test"}}
    mock_model.get_model_info.return_value = {"model": "test", "provider": "test"}
    
    mock_memory = MagicMock()
    mock_memory.process.return_value = "processed"
    
    mock_benchmark = AsyncMock()
    
    async def slow_benchmark():
        await asyncio.sleep(0.1)  # Small delay to test concurrency
        return {"score": 0.85}
    
    mock_benchmark.run_benchmark = slow_benchmark
    
    mock_registry.return_value.create_model.return_value = mock_model
    mock_registry.return_value.create_memory_method.return_value = mock_memory
    mock_registry.return_value.create_benchmark.return_value = mock_benchmark
    
    config = {
        "providers": {
            "test": {
                "models": ["model1", "model2"],
                "enabled_models": ["model1", "model2"],
                "temperature": 0.3
            }
        },
        "memory_methods": ["truncation"],
        "executed_benchmarks": ["benchmark1"],
        "benchmarks": {
            "benchmark1": {
                "temperature": 0.0,
                "max_tokens": 1000
            }
        },
        "concurrent_evaluations": 2
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        orchestrator = EvaluationOrchestrator(config, results_dir=temp_dir)
        
        import time
        start_time = time.time()
        summary = await orchestrator.run_full_evaluation()
        duration = time.time() - start_time
        
        assert summary["total_runs"] == 2
        assert summary["successful_runs"] == 2
        # With concurrency, should be faster than sequential
        assert duration < 0.25  # Should be much less than 0.2s (2 * 0.1s)
