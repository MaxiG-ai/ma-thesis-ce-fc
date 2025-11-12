"""
Orchestrator for running comprehensive evaluations across models, memory methods, and benchmarks.
"""

import asyncio
import itertools
import sys
from pathlib import Path
from typing import List, Dict, Any, Iterator, Tuple, Type
from datetime import datetime
import logging
from mcp_bench.mcpbench_adapter import MCPBenchAdapter
from nestful.nestful_adapter import NestfulAdapter

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.registry import ModelRegistry
from memory.registry import MemoryRegistry
from evaluation.results import ResultsStorage


logger = logging.getLogger(__name__)


class BenchmarkRegistry:
    """Registry for benchmark adapters."""
    
    _benchmarks: Dict[str, Type] = {}
    
    @classmethod
    def create_benchmark(cls, benchmark_name: str, **kwargs):
        """Create benchmark instance."""
        if benchmark_name not in cls._benchmarks:
            raise ValueError(f"Benchmark '{benchmark_name}' not registered")
        
        return cls._benchmarks[benchmark_name](**kwargs)
    
    @classmethod
    def register_benchmark(cls, name: str, benchmark_cls: Type) -> None:
        """Register a new benchmark."""
        cls._benchmarks[name] = benchmark_cls
    
    @classmethod
    def get_available_benchmarks(cls) -> List[str]:
        """Get available benchmark names."""
        return list(cls._benchmarks.keys())


class EvaluationOrchestrator:
    """Orchestrates evaluation runs across models, memory methods, and benchmarks."""
    
    def __init__(self, config: Dict[str, Any], results_dir: str = "results"):
        """
        Initialize the evaluation orchestrator.
        
        Args:
            config: Configuration dictionary containing models, memory methods, and benchmarks
            results_dir: Directory to store results
        """
        self.config = config
        self.results_storage = ResultsStorage(results_dir)
        
        # Load configuration into ModelRegistry
        ModelRegistry.load_from_config()
        
        # Auto-register benchmarks from config
        self._register_benchmarks_from_config()
        
        # Extract component lists from config
        self.model_specs = self._parse_model_specs()
        self.memory_methods = self.config.get("memory_methods", ["truncation"])
        self.benchmarks = self.config.get("executed_benchmarks", [])
        
        # Configuration options
        self.concurrent_evaluations = self.config.get("concurrent_evaluations", 1)
        
        # Log configuration summary
        providers_summary = {}
        for model_spec in self.model_specs:
            provider = model_spec["provider"]
            providers_summary[provider] = providers_summary.get(provider, 0) + 1
        
        logger.info(15*"###")
        logger.info("Initialized orchestrator:")
        logger.info(f"  Models: {len(self.model_specs)} total")
        for provider, count in providers_summary.items():
            logger.info(f"    {provider}: {count} models")
        logger.info(f"  Memory methods: {len(self.memory_methods)}")
        logger.info(f"  Benchmarks: {len(self.benchmarks)}")
    
    def _parse_model_specs(self) -> List[Dict[str, Any]]:
        """Parse model specifications from provider-specific configuration."""
        models = []
        
        # Get providers configuration
        providers_config = self.config.get("providers", {})
        
        if not providers_config:
            raise ValueError("No providers configured. Please add [providers.{name}] sections to config.")
        
        for provider_name, provider_config in providers_config.items():
            # Validate provider structure
            if not isinstance(provider_config, dict):
                continue
                
            available_models = provider_config.get("models", [])
            enabled_models = provider_config.get("enabled_models", [])
            
            # Validate enabled models are in available models
            invalid_models = set(enabled_models) - set(available_models)
            if invalid_models:
                raise ValueError(
                    f"Provider '{provider_name}' has invalid enabled models: {invalid_models}. "
                    f"Available models: {available_models}"
                )
            
            # Create model specs for enabled models
            for model_name in enabled_models:
                # Extract provider config (exclude model lists)
                provider_settings = {
                    k: v for k, v in provider_config.items() 
                    if k not in ["models", "enabled_models"]
                }
                
                models.append({
                    "name": model_name,
                    "provider": provider_name,
                    "config": provider_settings
                })
        
        if not models:
            raise ValueError("No models enabled. Please set enabled_models for at least one provider.")
        
        logger.info(f"Loaded {len(models)} enabled models across {len(providers_config)} providers")
        return models
    
    def _register_benchmarks_from_config(self):
        """Automatically register benchmarks based on config file."""
        benchmark_configs = self.config.get("executed_benchmarks", [])
        logger.info(f"Registering benchmarks from config: {benchmark_configs}")

        for benchmark_name in benchmark_configs:
            try:
                if benchmark_name == "nestful":
                    from evaluation.nestful.nestful_adapter import NestfulAdapter
                    BenchmarkRegistry.register_benchmark("nestful", NestfulAdapter)
                    logger.debug(f"Registered benchmark: {benchmark_name}")
                elif benchmark_name == "mcpbench":
                    from evaluation.mcp_bench.mcpbench_adapter import MCPBenchAdapter
                    BenchmarkRegistry.register_benchmark("mcpbench", MCPBenchAdapter)
                    logger.debug(f"Registered benchmark: {benchmark_name}")
                else:
                    logger.warning(f"Unknown benchmark '{benchmark_name}' in config - skipping")
            except ImportError as e:
                logger.error(f"Failed to import adapter for benchmark '{benchmark_name}': {e}")
            except Exception as e:
                logger.error(f"Failed to register benchmark '{benchmark_name}': {e}")
    
    def _generate_combinations(self) -> Iterator[Tuple[Dict[str, Any], str, str]]:
        """Generate all combinations of models × memory methods × benchmarks."""
        return itertools.product(self.model_specs, self.memory_methods, self.benchmarks)
    
    async def run_full_evaluation(self) -> Dict[str, Any]:
        """Run all combinations of models × memory methods × benchmarks."""
        
        combinations = list(self._generate_combinations())
        total_runs = len(combinations)
        
        logger.info(f"Starting evaluation with {total_runs} total combinations")
        logger.info(f"Concurrent evaluations: {self.concurrent_evaluations}")
        
        results = []
        
        if self.concurrent_evaluations == 1:
            # Sequential execution
            for i, (model_spec, memory_method, benchmark) in enumerate(combinations, 1):
                logger.info(f"Running evaluation {i}/{total_runs}: "
                           f"{model_spec['name']} × {memory_method} × {benchmark}")
                
                result = await self._run_single_evaluation_with_error_handling(
                    model_spec, memory_method, benchmark
                )
                results.append(result)
                
                # Save intermediate results
                self.results_storage.save_result(result)
        else:
            # Concurrent execution
            semaphore = asyncio.Semaphore(self.concurrent_evaluations)
            
            async def run_with_semaphore(combo_data):
                model_spec, memory_method, benchmark = combo_data
                async with semaphore:
                    result = await self._run_single_evaluation_with_error_handling(
                        model_spec, memory_method, benchmark
                    )
                    self.results_storage.save_result(result)
                    return result
            
            tasks = [run_with_semaphore(combo) for combo in combinations]
            results = await asyncio.gather(*tasks)
        
        # Generate summary report
        summary = self._generate_summary(results)
        
        logger.info("Evaluation completed!")
        logger.info(f"Total runs: {summary['total_runs']}")
        logger.info(f"Successful: {summary['successful_runs']}")
        logger.info(f"Failed: {summary['failed_runs']}")
        logger.info(f"Success rate: {summary['success_rate']:.2%}")
        
        return summary
    
    async def _run_single_evaluation_with_error_handling(
        self, 
        model_spec: Dict[str, Any], 
        memory_method: str, 
        benchmark: str
    ) -> Dict[str, Any]:
        """Run single evaluation with comprehensive error handling."""
        try:
            return await self._run_single_evaluation(model_spec, memory_method, benchmark)
        except Exception as e:
            error_context = {
                "model": model_spec['name'],
                "provider": model_spec.get('provider', 'unknown'),
                "memory_method": memory_method,
                "benchmark": benchmark,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
            
            logger.error(f"Failed evaluation {model_spec['name']} × {memory_method} × {benchmark}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.exception("Full error traceback:")
            
            return self._create_error_result(model_spec, memory_method, benchmark, error_context)
    
    async def _run_single_evaluation(
        self, 
        model_spec: Dict[str, Any], 
        memory_method: str, 
        benchmark: str
    ) -> Dict[str, Any]:
        """Run a single model × memory × benchmark combination."""
        
        start_time = datetime.now()
        
        # Initialize components
        model = ModelRegistry.create_model(
            provider=model_spec["provider"],
            model_name=model_spec["name"],
            **model_spec.get("config", {})
        )
        
        memory = MemoryRegistry.create_method(
            method_name=memory_method,
            **self.config.get("memoryMethods", {}).get(memory_method, {})
        )
        
        # Get benchmark configuration from the new structure
        benchmark_config = self.config.get("benchmarks", {}).get(benchmark, {})
        
        # Create benchmark instance with model, memory, and configuration
        benchmark_instance = BenchmarkRegistry.create_benchmark(
            benchmark_name=benchmark,
            model_instance=model,
            memory_instance=memory,
            benchmark_config=benchmark_config
        )
        
        # Execute real benchmark
        benchmark_results = await benchmark_instance.run_benchmark()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return {
            "timestamp": start_time.isoformat(),
            "duration_seconds": duration,
            "model": model_spec,
            "memory_method": memory_method,
            "benchmark": benchmark,
            "results": benchmark_results,
            "status": "success"
        }
    
    def _create_error_result(
        self, 
        model_spec: Dict[str, Any], 
        memory_method: str, 
        benchmark: str, 
        error: Any
    ) -> Dict[str, Any]:
        """Create error result entry with support for both string and structured error data."""
        return {
            "timestamp": datetime.now().isoformat(),
            "model": model_spec,
            "memory_method": memory_method,
            "benchmark": benchmark,
            "error": error,
            "status": "error"
        }
    
    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate evaluation summary."""
        successful = [r for r in results if r.get("status") == "success"]
        failed = [r for r in results if r.get("status") == "error"]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_runs": len(results),
            "successful_runs": len(successful),
            "failed_runs": len(failed),
            "success_rate": len(successful) / len(results) if results else 0,
            "results": results,
            "models_tested": list(set(r["model"]["name"] for r in results)),
            "memory_methods_tested": list(set(r["memory_method"] for r in results)),
            "benchmarks_tested": list(set(r["benchmark"] for r in results))
        }
