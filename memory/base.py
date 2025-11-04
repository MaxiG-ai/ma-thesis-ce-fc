"""
Abstract base class for memory methods.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseMemoryMethod(ABC):
    """Abstract base class for all memory management methods."""
    
    @abstractmethod
    def process(self, text: str, **kwargs) -> str:
        """
        Process text according to the memory method's strategy.
        
        Args:
            text: The input text to process
            **kwargs: Method-specific parameters
            
        Returns:
            Processed text according to the memory method
        """
        pass
    
    @abstractmethod
    def get_method_info(self) -> Dict[str, Any]:
        """
        Return information about this memory method.
        
        Returns:
            Dict containing:
            - method: str (method name)
            - version: str (method version)
            - parameters: list (supported parameters)
            - description: str (method description)
        """
        pass
