from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any


class TaskAdapter(ABC):
    """
    Abstract base class for dataset-specific adapters.

    Each adapter is responsible for:
    1. Loading tasks from its dataset
    2. Executing tasks with a given model
    3. Evaluating and scoring results
    """

    @abstractmethod
    def load_tasks(
        self, dataset_path: str, filters: Optional[Dict] = None
    ) -> List[UnifiedTask]:
        """
        Load tasks from the dataset.

        Args:
            dataset_path: Path to dataset directory/file
            filters: Optional filter criteria (dataset-specific)

        Returns:
            List of UnifiedTask objects
        """
        pass

    @abstractmethod
    def execute_task(
        self, task: UnifiedTask, context: ExecutionContext
    ) -> Tuple[Any, Dict[str, Any]]:
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
    def evaluate_result(self, task: UnifiedTask, raw_output: Any) -> bool:
        """
        Evaluate whether the task result is correct.

        Args:
            task: The task that was executed
            raw_output: The raw output from execution

        Returns:
            Boolean indicating success
        """
        pass
