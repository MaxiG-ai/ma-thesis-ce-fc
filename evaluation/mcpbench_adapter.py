"""
MCP Bench Benchmark Adapter.

This module provides the adapter for integrating MCP Benchmark runner
with the config-driven evaluation system.
"""
import sys
import json
import logging
import tomllib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.BenchmarkAdapter import BenchmarkAdapter
from datasets.mcp_bench.benchmark.runner import BenchmarkRunner
from datasets.mcp_bench.benchmark.evaluator import TaskEvaluator
from datasets.mcp_bench.utils.local_server_config import LocalServerConfigLoader

logger = logging.getLogger(__name__)


class MCPBenchAdapter(BenchmarkAdapter):
    """
    Adapter for MCP Benchmark evaluation.
    
    This adapter integrates the MCP Benchmark runner with the config-driven
    evaluation system, providing a standardized interface for running benchmarks
    and evaluating results.
    
    Attributes:
        config: Configuration dictionary from TOML file
        model_provider: LLM provider name (e.g., "ollama", "openai")
        model_name: Single model name or None if using model_names
        model_names: List of model names for multi-model runs
        tasks_file: Path to tasks JSON file
        temperature: Temperature for LLM generation
        max_tokens: Maximum tokens for LLM generation
        task_limit: Optional limit on number of tasks
        enable_distraction_servers: Whether to include distraction servers
        distraction_count: Number of distraction servers
        enable_judge_stability: Whether to enable judge stability checks
        filter_problematic_tools: Whether to filter problematic tools
        concurrent_summarization: Whether to summarize concurrently
        use_fuzzy_descriptions: Whether to use fuzzy descriptions
        save_directory: Directory for saving results
    """
    
    # Required config fields
    REQUIRED_FIELDS = ["model", "model_name", "tasks_file"]
    
    # Default values for optional fields
    DEFAULTS = {
        "temperature": 0.3,
        "max_tokens": 1000,
        "task_limit": None,
        "enable_distraction_servers": False,
        "distraction_count": 0,
        "enable_judge_stability": True,
        "filter_problematic_tools": True,
        "concurrent_summarization": True,
        "use_fuzzy_descriptions": False,
        "save_directory": "results/mcpbench",
        "model_names": None,
    }
    
    # Supported model providers
    SUPPORTED_PROVIDERS = ["ollama", "openai", "azure", "anthropic"]
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the MCP Bench adapter.
        
        Args:
            config: Configuration dictionary with benchmark settings
            
        Raises:
            ValueError: If required config fields are missing or invalid
        """
        self.config = config
        self._validate_config()
        self._load_config_values()
        self._runner = None
        self._evaluator = None
    
    def _validate_config(self) -> None:
        """Validate that required config fields are present and valid."""
        # Check required fields (excluding model_name if model_names is provided)
        for field in self.REQUIRED_FIELDS:
            if field == "model_name" and "model_names" in self.config:
                continue  # model_names can substitute for model_name
            if field not in self.config:
                raise ValueError(f"Missing required config field: {field}")
        
        # Validate tasks_file
        tasks_file = self.config.get("tasks_file", "")
        if not tasks_file or not isinstance(tasks_file, str):
            raise ValueError("tasks_file cannot be empty")
    
    def _load_config_values(self) -> None:
        """Load configuration values with defaults."""
        # Apply defaults
        for key, default_value in self.DEFAULTS.items():
            setattr(self, key, self.config.get(key, default_value))

        # Read commands json path from config (optional). Default to the
        # workspace-relative commands.json inside the datasets package so
        # relative code that used "mcp_servers/commands.json" continues to work
        # when invoked from project root.
        self.commands_json_path = self.config.get(
            "commands_json_path",
            "datasets/mcp_bench/mcp_servers/commands.json"
        )
        
        # Load core fields
        self.model_provider = self.config["model"]
        self.model_name = self.config.get("model_name")
        self.model_names = self.config.get("model_names")
        self.tasks_file = self.config["tasks_file"]
    
    def _validate_model_provider(self) -> None:
        """
        Validate that the model provider is supported.
        
        Raises:
            ValueError: If model provider is not supported
        """
        if self.model_provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported model provider: {self.model_provider}. "
                f"Supported providers: {', '.join(self.SUPPORTED_PROVIDERS)}"
            )
    
    def get_selected_models(self) -> List[str]:
        """
        Get the list of models to run.
        
        Returns:
            List of model names
        """
        if self.model_names:
            return self.model_names
        elif self.model_name:
            return [self.model_name]
        else:
            raise ValueError("Either model_name or model_names must be specified")
    
    @classmethod
    def load_config_from_file(
        cls,
        config_path: str,
        section: str = "mcpbench"
    ) -> Dict[str, Any]:
        """
        Load configuration from a TOML file.
        
        Args:
            config_path: Path to the TOML configuration file
            section: Section name in the TOML file (default: "mcpbench")
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If section is not found in config
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_file, "rb") as f:
            full_config = tomllib.load(f)
        
        if section not in full_config:
            raise ValueError(
                f"Section '{section}' not found in config file. "
                f"Available sections: {', '.join(full_config.keys())}"
            )
        
        return full_config[section]
    
    async def run_benchmark(
        self,
        selected_models: Optional[List[str]] = None,
        task_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute benchmark tasks using the specified model(s).
        
        Args:
            selected_models: Optional list of model names to run. If None, uses config.
            task_limit: Optional limit on number of tasks. If None, uses config.
            
        Returns:
            Dict containing benchmark results with standardized format:
            - models: Dict[model_name, results] with task results per model
            - metadata: Dict with timestamp, config, and aggregate metrics
        """
        # Determine which models to run
        if selected_models is None:
            selected_models = self.get_selected_models()
        
        # Determine task limit
        if task_limit is None:
            task_limit = self.task_limit
        
        # Initialize benchmark runner
        # Create a LocalServerConfigLoader with the configured commands.json
        # path and inject it into the BenchmarkRunner so the loader doesn't
        # try to open the old hard-coded relative path.
        local_loader = LocalServerConfigLoader(commands_json_path=self.commands_json_path)

        self._runner = BenchmarkRunner(
            tasks_file=self.tasks_file,
            enable_distraction_servers=self.enable_distraction_servers,
            distraction_count=self.distraction_count,
            enable_judge_stability=self.enable_judge_stability,
            filter_problematic_tools=self.filter_problematic_tools,
            concurrent_summarization=self.concurrent_summarization,
            use_fuzzy_descriptions=self.use_fuzzy_descriptions,
            local_config_loader=local_loader,
        )
        
        logger.info(f"Running MCP Bench with models: {selected_models}")
        logger.info(f"Task limit: {task_limit if task_limit else 'all tasks'}")
        
        # Run benchmark
        results = await self._runner.run_benchmark(
            selected_models=selected_models,
            task_limit=task_limit
        )
        
        return results
    
    def evaluate_result(
        self,
        task: Dict[str, Any],
        execution_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate whether the task result is correct.
        
        Args:
            task: The task that was executed (with expected outputs/ground truth)
            execution_result: The raw output from execution
            
        Returns:
            Dict containing:
            - success: bool indicating overall success
            - overall_score: float (0.0-1.0) indicating quality
            - schema_understanding: float score for schema understanding
            - task_completion: float score for task completion
            - tool_usage: float score for tool usage
            - planning_effectiveness: float score for planning
            - details: Dict with additional evaluation details
            
        Raises:
            ValueError: If task or execution_result is None
        """
        if task is None:
            raise ValueError("task cannot be None")
        if execution_result is None:
            raise ValueError("execution_result cannot be None")
        
        # Initialize evaluator with config if not already done
        if self._evaluator is None:
            # Load judge provider from config if specified
            judge_config = self.config.get("judge_config", {})
            self._evaluator = TaskEvaluator(
                enable_judge_stability=self.enable_judge_stability,
                judge_config=judge_config
            )
        
        # Perform evaluation
        eval_result = self._evaluator.evaluate_task(
            task=task,
            execution_result=execution_result
        )
        
        # Standardize the result format
        standardized_result = {
            "success": execution_result.get("success", False),
            "overall_score": eval_result.get("overall_score", 0.0),
            "schema_understanding": eval_result.get("schema_understanding", 0.0),
            "task_completion": eval_result.get("task_completion", 0.0),
            "tool_usage": eval_result.get("tool_usage", 0.0),
            "planning_effectiveness": eval_result.get("planning_effectiveness", 0.0),
            "details": eval_result.get("details", {})
        }
        
        return standardized_result
    
    async def save_results(
        self,
        results: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """
        Save benchmark results to a JSON file.
        
        Args:
            results: Results dictionary to save
            filename: Optional custom filename. If None, generates timestamped name.
            
        Returns:
            Path to the saved results file
        """
        # Create output directory if it doesn't exist
        output_dir = Path(self.save_directory)
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
