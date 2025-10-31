from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any


class BenchmarkAdapter(ABC):
    """
    Abstract base class for dataset-specific adapters.

    Each adapter is responsible for:
    1. Loading tasks from its dataset
    2. Executing tasks with a given model
    3. Evaluating and scoring results
    """

    @abstractmethod
    def run_benchmark(
        self, 
    ):
        """
        Execute a single task using the specified model.

        Args:
            task: The task to execute
            context: Execution context (model, config, etc.)

        Returns:
            Tuple of (raw_output, metrics_dict) where metrics_dict contains:
            - token_usage: int (total tokens used)
            - time_taken: float (seconds)
            - Any other relevant metrics
        """
        pass

    @abstractmethod
    def evaluate_result(self):
        """
        Evaluate whether the task result is correct.

        Args:
            task: The task that was executed
            raw_output: The raw output from execution

        Returns:
            Boolean indicating success
        """
        pass
