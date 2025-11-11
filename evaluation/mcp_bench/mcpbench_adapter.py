"""
MCP Bench Benchmark Adapter.

This module provides the adapter for integrating MCP Benchmark runner
with the config-driven evaluation system.
"""
import sys
import json
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, cast
from types import SimpleNamespace

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.BenchmarkAdapter import BenchmarkAdapter
from datasets.mcp_bench.benchmark.runner import (
    BenchmarkRunner,
    ConnectionManager,
    _determine_selected_models,
    _print_configuration,
)
from datasets.mcp_bench.utils.local_server_config import LocalServerConfigLoader
from evaluation.mcp_bench.path_adjusted_server_manager import PathAdjustedServerManager
from evaluation.mcp_bench.path_adjusted_connection_manager import PathAdjustedConnectionManager

from models.registry import ModelRegistry

logger = logging.getLogger(__name__)


class MCPBenchAdapter(BenchmarkAdapter):
    """Adapter for MCP Benchmark evaluation."""
    
    def __init__(self, model_instance=None, memory_instance=None, benchmark_config=None, config_path: str = "evaluation/config.toml"):
        """Initialize the MCP Bench adapter.
        
        Args:
            model_instance: Model instance from orchestrator (preferred)
            memory_instance: Memory method instance from orchestrator (preferred)  
            benchmark_config: Benchmark configuration from orchestrator (preferred)
            config_path: Path to config.toml file for legacy mode
        """
        # Handle orchestrator mode vs legacy mode
        if model_instance is not None and benchmark_config is not None:
            # Orchestrator mode - use passed instances and config
            self.model_instance = model_instance
            self.memory_instance = memory_instance
            self.cfg = benchmark_config
            self.orchestrator_mode = True
        else:
            # Legacy mode - load from config file
            super().__init__("benchmarks.mcpbench", config_path)
            self.model_instance = None
            self.memory_instance = None
            self.orchestrator_mode = False
            
        self._runner = None
        self._last_results = None

    ### LIMITING TASKS ###
    # it seems tasks can either be limited by
    # - changing the task file
    # - overriding the class BenchmarkRunner to accept a task limit 

    ### MCP SERVER CONFIGURATION ###
    # Read by `load_server_configs()` -> Should als be in config.toml

    ### MCP SERVER COMMANDS ###
    # Read by `load_commands_config()` -> TODO: Currently not working because of PATH issues

    ### EXECUTE TASKS ###
    # implemented in `execute_single_task_with_model()` in BenchmarkRunner

    ### RUN BENCHMARK ###
    # `_run_single_file_benchmark_core` in BenchmarkRunner

    # Questions:
    # - How to handle distraction servers?
    # - Where to handle the LLM as a judge server?

    # TODO: replace Step 1: with config-driven approach

    def get_selected_models(self) -> List[str]:
        """Get the list of models to run."""
        if "model_names" in self.cfg:
            return self.cfg["model_names"]
        raise ValueError("model_names must be specified in the configuration")

    def parse_arguments_from_config(self) -> SimpleNamespace:
        """Create an args namespace from config.toml instead of command line arguments."""
        args = SimpleNamespace()
        
        # Model selection
        args.models = self.cfg.get("model_names", ["o4-mini"])
        args.list_models = False  # This is a command-line only flag
        
        # File paths
        args.tasks_file = self.cfg.get("tasks_file", None)
        args.output = self.cfg.get("output", None)
        
        # Logging
        args.verbose = self.cfg.get("verbose", False)
        
        # Server configuration
        args.distraction_count = self.cfg.get("distraction_count", 10)
        
        # Feature toggles (note: config uses enable_*, args uses disable_*)
        args.disable_judge_stability = not self.cfg.get("enable_judge_stability", True)
        args.disable_filter_problematic_tools = not self.cfg.get("filter_problematic_tools", True)
        args.disable_concurrent_summarization = not self.cfg.get("concurrent_summarization", True)
        args.disable_fuzzy = not self.cfg.get("use_fuzzy_descriptions", False)
        
        # Cache configuration
        args.enable_cache = self.cfg.get("enable_cache", False)
        args.cache_ttl = self.cfg.get("cache_ttl", 0)
        args.cache_dir = self.cfg.get("cache_dir", "./cache")
        
        return args

    async def create_config_aware_runner_and_get_models(self, args, tasks_file, enable_distraction_servers):
        """Create a BenchmarkRunner with all config values properly injected from config.toml"""
        
        # Monkey-patch the runner module to use our PathAdjustedConnectionManager
        # This allows the runner to automatically adjust paths without modifying the submodule
        import datasets.mcp_bench.benchmark.runner as runner_module
        runner_module.ConnectionManager = PathAdjustedConnectionManager
        logger.info("Patched ConnectionManager to use PathAdjustedConnectionManager for path adjustment")
        
        # Create config-aware LocalServerConfigLoader with correct paths
        local_config_loader = LocalServerConfigLoader(
            commands_json_path=self.cfg.get("server_commands_path", "datasets/mcp_bench/mcp_servers/commands.json"),
            api_key_path=self.cfg.get("server_api_keys_path", "datasets/mcp_bench/mcp_servers/api_key")
        )
        
        # Load model registry and configs
        model_registry = ModelRegistry()
        model_registry.load_from_config("evaluation/config.toml")
        model_configs = model_registry.get_model_configs()
        
        # Create judge provider from config
        judge_model_name = self.cfg.get("judge_model", "meta-llama/llama-3.3-8b-instruct:free")
        logger.info(f"Initializing judge model: {judge_model_name}")
        
        if judge_model_name not in model_configs:
            available = list(model_configs.keys())
            raise ValueError(
                f"Judge model '{judge_model_name}' not found in available models. "
                f"Available models: {available}"
            )
        
        # Import LLMFactory and ModelConfig to create judge provider
        from datasets.mcp_bench.llm.factory import LLMFactory, ModelConfig
        
        # Get our registry's model config and convert to MCP Bench's ModelConfig
        registry_config = model_configs[judge_model_name]
        
        # Create MCP Bench compatible ModelConfig
        judge_model_config = ModelConfig(
            name=registry_config.name,
            provider_type=registry_config.provider_type,
            **registry_config.config
        )
        
        judge_provider = await LLMFactory.create_llm_provider(judge_model_config)
        logger.info(f"Judge provider created successfully for model: {judge_model_name}")
        
        # Create BenchmarkRunner with all config values explicitly set to avoid defaults
        runner = BenchmarkRunner(
            tasks_file=tasks_file,
            enable_distraction_servers=enable_distraction_servers,
            distraction_count=self.cfg.get("distraction_count", 0),
            enable_judge_stability=self.cfg.get("enable_judge_stability", True),
            filter_problematic_tools=self.cfg.get("filter_problematic_tools", True),
            concurrent_summarization=self.cfg.get("concurrent_summarization", True),
            use_fuzzy_descriptions=self.cfg.get("use_fuzzy_descriptions", False),
            local_config_loader=local_config_loader,  # Inject config-aware loader
            judge_provider=judge_provider,  # Inject judge provider
        )
        
        # Always load commands_config to avoid NoneType errors in _prepare_server_configs
        # The runner checks self.commands_config even when distraction is disabled
        runner.commands_config = await runner.load_commands_config()
        logger.info(f"Loaded commands configuration: {len(runner.commands_config)} servers")

        
        # Cast registry model configs to a generic mapping to satisfy static type checkers
        runner.model_configs = cast(Dict[str, Any], model_configs)
        
        # Get available models from the runner
        available_models = list(runner.model_configs.keys())
        
        return runner, available_models

    async def run_benchmark(
        self,
    ) -> Dict[str, Any]:
        """
        Execute benchmark tasks using the specified model(s).
        Implementation of the abstract method from BenchmarkAdapter.
        """
        # Handle demo mode - modify task limit
        original_task_limit = None
        if self.cfg.get("demo", False):
            logger.info("Demo mode: Running with 1 random task")
            # Override task_limit for demo mode
            original_task_limit = self.cfg.get("task_limit")
            self.cfg["task_limit"] = 1
        
        # Step 1 - Parse and validate arguments pulled from `config.toml`
        args = self.parse_arguments_from_config()
        tasks_file = self.cfg.get("tasks_file", None)
        enable_distraction_servers = args.distraction_count > 0
        
        logger.info(f"Using tasks file: {tasks_file}")

        # Step 2 - Create runner and get models using config-aware factory
        self._runner, self._selected_models = await self.create_config_aware_runner_and_get_models(
            args, tasks_file, enable_distraction_servers
        )

        # Log the models used
        if args.list_models:
            print("Available models:")
            for i, model in enumerate(self._selected_models, 1):
                print(f"  {i:2d}. {model}")
            print(f"\nTotal: {len(self._selected_models)} models")
            print("\nUsage examples:")
            print(f"  python {sys.argv[0]} --models {self._selected_models[0] if self._selected_models else 'MODEL_NAME'}")

        # Step 3: Determine which models to test
        if self.orchestrator_mode and self.model_instance is not None:
            # Use the model name from orchestrator
            model_info = self.model_instance.get_model_info()
            # get_model_info() returns {'model': model_name, 'provider': provider_name}
            model_name = model_info.get("model", "unknown") if isinstance(model_info, dict) else "unknown"
            selected_models = [model_name]
            logger.info(f"Orchestrator mode: using model '{model_name}' from model instance")
        else:
            selected_models = _determine_selected_models(args, self._selected_models)

        # Step 4: Print configuration
        _print_configuration(selected_models, self._selected_models, self._runner, args)

        # Step 5: Run benchmark
        try:
            logger.info("Starting multi-model benchmark execution...")
            results = await self._runner.run_benchmark(
                selected_models=selected_models, 
                # task_limit=task_limit
            )
            
            # Save results to JSON file (only if not in demo mode)
            if results and not self.cfg.get("demo", False):
                output_file = args.output if args.output else f'benchmark_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2, ensure_ascii=False)
                    logger.info(f"Results saved to {output_file}")
                    logger.info("The overall score is calculated as the average of four main dimensions: schema understanding, task completion, tool usage, and planning effectiveness. Within each dimension (e.g., schema understanding), we first compute the mean across its sub-dimensions.")
                except Exception as save_error:
                    logger.error(f"Failed to save results to {output_file}: {save_error}")
            
            # Add demo mode indicator to results
            if results and self.cfg.get("demo", False):
                if "metadata" not in results:
                    results["metadata"] = {}
                results["metadata"]["demo_mode"] = True
                    
            return results
    
        except Exception as e:
            logger.error(f"ERROR in multi-model benchmark execution: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
        finally:
            # Restore original task_limit if demo mode was used
            if self.cfg.get("demo", False):
                if 'original_task_limit' in locals():
                    self.cfg["task_limit"] = original_task_limit

    def evaluate_result(self):
        return super().evaluate_result()
    
    async def save_results(
        self,
        results: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """Save benchmark results to a JSON file."""
        # Create output directory if it doesn't exist
        output_dir = Path(self.cfg.get("results_dir", "results/mcpbench"))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mcpbench_results_{timestamp}.json"
        
        # Full output path
        output_path = output_dir / filename
        
        # Save results
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {output_path}")
        return str(output_path)
