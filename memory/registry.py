"""
Registry for memory methods.
"""

from typing import Dict, Type, List, Any
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from memory.base import BaseMemoryMethod
from memory.methods.truncation_memory import TruncationMemory


class MemoryRegistry:
    """Central registry for memory method discovery and creation."""
    
    _methods: Dict[str, Type[BaseMemoryMethod]] = {
        "truncation": TruncationMemory,
    }
    
    @classmethod
    def create_method(cls, method_name: str, **kwargs) -> BaseMemoryMethod:
        """
        Factory method to create memory method instances.
        
        Args:
            method_name: Name of the memory method to create
            **kwargs: Configuration parameters for the method
            
        Returns:
            Instance of the specified memory method
            
        Raises:
            ValueError: If method_name is not registered
        """
        if method_name not in cls._methods:
            raise ValueError(f"Memory method '{method_name}' not registered")
        
        return cls._methods[method_name](**kwargs)
    
    @classmethod
    def register_method(cls, name: str, method_cls: Type[BaseMemoryMethod]) -> None:
        """
        Register a new memory method.
        
        Args:
            name: Name to register the method under
            method_cls: Memory method class that inherits from BaseMemoryMethod
        """
        cls._methods[name] = method_cls
    
    @classmethod
    def get_available_methods(cls) -> List[str]:
        """
        Get list of available memory method names.
        
        Returns:
            List of registered memory method names
        """
        return list(cls._methods.keys())
    
    @classmethod
    def get_method_info(cls, method_name: str) -> Dict[str, Any]:
        """
        Get information about a specific memory method.
        
        Args:
            method_name: Name of the memory method
            
        Returns:
            Dictionary containing method information
            
        Raises:
            ValueError: If method_name is not registered
        """
        if method_name not in cls._methods:
            raise ValueError(f"Memory method '{method_name}' not registered")
        
        # Create a temporary instance to get method info
        temp_instance = cls._methods[method_name]()
        return temp_instance.get_method_info()
    
    @classmethod
    def list_all_methods(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all registered memory methods.
        
        Returns:
            Dictionary mapping method names to their information
        """
        all_methods = {}
        for method_name in cls._methods:
            all_methods[method_name] = cls.get_method_info(method_name)
        
        return all_methods
