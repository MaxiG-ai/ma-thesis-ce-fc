from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
import tomllib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class BenchmarkAdapter(ABC):
    """
    Abstract base class for dataset-specific adapters.

    Each adapter is responsible for:
    1. Loading tasks from its dataset
    2. Executing tasks with a given model
    3. Evaluating and scoring results
    """

    def __init__(self, section_name: str, config_path: str = "evaluation/config.toml"):
        """
        Initialize adapter with automatic config loading.

        Args:
            section_name: Name of the config section to load
            config_path: Path to the TOML config file
        """
        self.cfg = self._load_config(config_path, section_name)

    def _load_config(self, config_path: str, section_name: str) -> Dict[str, Any]:
        """Load configuration from TOML file."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_file, "rb") as f:
            full_config = tomllib.load(f)

        if section_name not in full_config:
            raise ValueError(f"Section '{section_name}' not found in config file")

        # Start with section config and add top-level model_names if present
        cfg = dict(full_config[section_name])
        if "model_names" in full_config:
            cfg["model_names"] = full_config["model_names"]

        return cfg

    def print_config(self) -> None:
        """Print configuration to logger.info."""
        logger.info("=" * 60)
        logger.info("Configuration")
        logger.info("=" * 60)
        for key, value in self.cfg.items():
            logger.info(f"{key}: {value}")
        logger.info("=" * 60)

    @abstractmethod
    async def run_benchmark(
        self,
    ) -> Dict[str, Any]:
        """
        Execute benchmark tasks using the specified model(s).

        Args:
            selected_models: Optional list of model names to run. If None, uses config default.
            task_limit: Optional limit on number of tasks to run. If None, runs all tasks.

        Returns:
            Dict containing:
            - models: Dict[model_name, results] with task results per model
            - metadata: Dict with timestamp, config, and aggregate metrics
            - Any other benchmark-specific data
        """
        pass

    @abstractmethod
    def evaluate_result(self):
        """
        Evaluate whether the task result is correct.

        Args:
            task: The task that was executed (with expected outputs/ground truth)
            execution_result: The raw output from execution

        Returns:
            Dict containing:
            - success: bool indicating overall success
            - score: float (0.0-1.0) indicating quality
            - details: Dict with dimension-specific scores and reasoning
        """
        pass
