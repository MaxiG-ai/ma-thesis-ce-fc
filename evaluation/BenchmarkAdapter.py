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
    async def run_benchmark(
        self,
        selected_models: Optional[List[str]] = None,
        task_limit: Optional[int] = None
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
            - score: float (0.0-1.0) indicating quality
            - details: Dict with dimension-specific scores and reasoning
        """
        pass
