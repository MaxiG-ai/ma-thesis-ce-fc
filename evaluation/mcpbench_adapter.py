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
from typing import Dict, List, Any, Optional
from types import SimpleNamespace

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.BenchmarkAdapter import BenchmarkAdapter
from datasets.mcp_bench.benchmark.runner import (
    _create_runner_and_get_models,
    _determine_selected_models,
    _print_configuration,

)

logger = logging.getLogger(__name__)


class MCPBenchAdapter(BenchmarkAdapter):
    """Adapter for MCP Benchmark evaluation."""
    
    def __init__(self, config_path: str = "evaluation/config.toml"):
        """Initialize the MCP Bench adapter.
        
        Args:
            config_path: Path to config.toml file. Defaults to "evaluation/config.toml".
        """
        super().__init__("mcpbench", config_path)
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

    def parse_and_validate_args_from_config(self) -> tuple[SimpleNamespace, str, bool]:
        """Config-driven replacement of _parse_and_validate_args from runner.py."""
        args = self.parse_arguments_from_config()
        
        # Configure logging
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Use provided file paths
        tasks_file = args.tasks_file
        
        # Check if files exist (handle comma-separated files)
        if tasks_file:
            if ',' in tasks_file:
                # Multiple files specified
                task_files = [f.strip() for f in tasks_file.split(',')]
                for task_file in task_files:
                    if not os.path.exists(task_file):
                        logger.error(f"Tasks file not found: {task_file}")
                        raise FileNotFoundError(f"Tasks file not found: {task_file}")
            else:
                # Single file specified
                if not os.path.exists(tasks_file):
                    logger.error(f"Tasks file not found: {tasks_file}")
                    raise FileNotFoundError(f"Tasks file not found: {tasks_file}")
        
        # Determine if distraction is enabled based on count
        enable_distraction = args.distraction_count > 0
        
        return args, tasks_file, enable_distraction

    async def run_benchmark(
        self,
    ) -> Dict[str, Any]:
        """
        Execute benchmark tasks using the specified model(s).
        Implementation of the abstract method from BenchmarkAdapter.
        """
        # Step 1 - Parse and validate arguments pulled from `config.toml`
        args, tasks_file, enable_distraction_servers = self.parse_and_validate_args_from_config()

        # Step 2 - Create runner and get models
        self._runner, self._selected_models = _create_runner_and_get_models(
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
            
            # Save results to JSON file
            if results:
                output_file = args.output if args.output else f'benchmark_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2, ensure_ascii=False)
                    logger.info(f"Results saved to {output_file}")
                    logger.info("The overall score is calculated as the average of four main dimensions: schema understanding, task completion, tool usage, and planning effectiveness. Within each dimension (e.g., schema understanding), we first compute the mean across its sub-dimensions.")
                except Exception as save_error:
                    logger.error(f"Failed to save results to {output_file}: {save_error}")
                    
            return results
    
        except Exception as e:
            logger.error(f"ERROR in multi-model benchmark execution: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

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
