"""
Orchestrator for running comprehensive evaluations across models, memory methods, and benchmarks.
"""

import asyncio
import itertools
import sys
from pathlib import Path
from typing import List, Dict, Any, Iterator, Tuple
from datetime import datetime
import logging

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from evaluation.registries import ComponentRegistry
from evaluation.results import ResultsStorage

logger = logging.getLogger(__name__)


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
        self.registry = ComponentRegistry()
        
        # Update model registry with configuration
        providers_config = self.config.get("providers", {})
        if providers_config:
            from models.registry import ModelRegistry
            ModelRegistry.update_provider_catalog(providers_config)
        
        # Extract component lists from config
        self.model_specs = self._parse_model_specs()
        self.memory_methods = self.config.get("memory_methods", ["truncation"])
        self.benchmarks = self.config.get("benchmarks", ["nestful"])
        
        # Configuration options
        self.concurrent_evaluations = self.config.get("concurrent_evaluations", 1)
        
        # Log configuration summary
        providers_summary = {}
        for model_spec in self.model_specs:
            provider = model_spec["provider"]
            providers_summary[provider] = providers_summary.get(provider, 0) + 1
        
        logger.info(f"Initialized orchestrator:")
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
        """Run single evaluation with error handling."""
        try:
            return await self._run_single_evaluation(model_spec, memory_method, benchmark)
        except Exception as e:
            logger.error(f"Failed evaluation {model_spec['name']} × {memory_method} × {benchmark}: {e}")
            return self._create_error_result(model_spec, memory_method, benchmark, str(e))
    
    async def _run_single_evaluation(
        self, 
        model_spec: Dict[str, Any], 
        memory_method: str, 
        benchmark: str
    ) -> Dict[str, Any]:
        """Run a single model × memory × benchmark combination."""
        
        start_time = datetime.now()
        
        # Initialize components
        model = self.registry.create_model(
            provider=model_spec["provider"],
            model_name=model_spec["name"],
            **model_spec.get("config", {})
        )
        
        memory = self.registry.create_memory_method(
            method_name=memory_method,
            **self.config.get(f"{memory_method}_config", {})
        )
        
        # For benchmarks, we need to determine the appropriate configuration
        benchmark_config = self.config.get(benchmark, {})
        
        # Create benchmark - for now we'll use a mock approach since we don't have 
        # concrete benchmark implementations registered
        # benchmark_instance = self.registry.create_benchmark(
        #     benchmark_name=benchmark,
        #     **benchmark_config
        # )
        
        # For now, simulate benchmark execution -> TODO: Integrate with real benchmarks
        benchmark_results = await self._simulate_benchmark_execution(
            model, memory, benchmark, benchmark_config
        )
        
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
    
    async def _simulate_benchmark_execution(
        self, 
        model, 
        memory, 
        benchmark: str, 
        benchmark_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate benchmark execution for testing purposes."""
        
        # Create a simple test prompt
        test_prompt = "What is artificial intelligence and how does it work?"
        
        # Apply memory processing
        processed_prompt = memory.process(test_prompt)
        
        # Generate response from model
        response = await model.generate_text(
            prompt=processed_prompt,
            system="You are a helpful AI assistant.",
            **benchmark_config.get("generation_params", {})
        )
        
        # Simulate evaluation metrics
        return {
            "prompt_length": len(test_prompt.split()),
            "processed_prompt_length": len(processed_prompt.split()),
            "response_length": len(response.get("message", {}).get("content", "").split()),
            "model_info": model.get_model_info(),
            "memory_info": memory.get_method_info(),
            "benchmark": benchmark,
            "score": 0.85,  # Simulated score
            "success": True
        }
    
    def _create_error_result(
        self, 
        model_spec: Dict[str, Any], 
        memory_method: str, 
        benchmark: str, 
        error: str
    ) -> Dict[str, Any]:
        """Create error result entry."""
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
