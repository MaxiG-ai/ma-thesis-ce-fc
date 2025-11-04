"""
Tests for the BaseMemoryMethod abstract base class.
"""

import pytest
from abc import ABC
from typing import Dict, Any

# Import will be available after we create the base class
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_base_memory_method_is_abstract():
    """Test that BaseMemoryMethod cannot be instantiated directly."""
    from memory.base import BaseMemoryMethod
    
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        BaseMemoryMethod()


def test_base_memory_method_has_required_methods():
    """Test that BaseMemoryMethod defines the required abstract methods."""
    from memory.base import BaseMemoryMethod
    
    # Check that the abstract methods exist
    assert hasattr(BaseMemoryMethod, 'process')
    assert hasattr(BaseMemoryMethod, 'get_method_info')
    
    # Check they are abstract
    assert BaseMemoryMethod.process.__isabstractmethod__
    assert BaseMemoryMethod.get_method_info.__isabstractmethod__


def test_concrete_implementation_must_implement_abstract_methods():
    """Test that concrete implementations must implement all abstract methods."""
    from memory.base import BaseMemoryMethod
    
    # Incomplete implementation - missing get_method_info
    class IncompleteMemoryMethod(BaseMemoryMethod):
        def process(self, text: str, **kwargs) -> str:
            return text
    
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IncompleteMemoryMethod()


def test_concrete_implementation_can_be_instantiated():
    """Test that a complete concrete implementation can be instantiated."""
    from memory.base import BaseMemoryMethod
    
    class CompleteMemoryMethod(BaseMemoryMethod):
        def __init__(self, **kwargs):
            self.config = kwargs
        
        def process(self, text: str, **kwargs) -> str:
            return f"processed: {text}"
        
        def get_method_info(self) -> Dict[str, Any]:
            return {"method": "complete", "version": "1.0"}
    
    # Should not raise an exception
    method = CompleteMemoryMethod(param1="value1")
    assert method is not None
    assert method.config == {"param1": "value1"}


def test_concrete_implementation_method_signatures():
    """Test that concrete implementations work with expected method signatures."""
    from memory.base import BaseMemoryMethod
    
    class TestMemoryMethod(BaseMemoryMethod):
        def process(self, text: str, **kwargs) -> str:
            max_length = kwargs.get('max_length', 100)
            return text[:max_length]
        
        def get_method_info(self) -> Dict[str, Any]:
            return {"method": "test", "parameters": ["max_length"]}
    
    method = TestMemoryMethod()
    
    # Test process method
    result = method.process("Hello world", max_length=5)
    assert result == "Hello"
    
    # Test get_method_info
    info = method.get_method_info()
    assert info["method"] == "test"
    assert "parameters" in info


def test_base_memory_method_inheritance():
    """Test the inheritance structure."""
    from memory.base import BaseMemoryMethod
    
    # Should inherit from ABC
    assert issubclass(BaseMemoryMethod, ABC)
    
    class ConcreteMethod(BaseMemoryMethod):
        def process(self, text: str, **kwargs) -> str:
            return text
        
        def get_method_info(self) -> Dict[str, Any]:
            return {}
    
    method = ConcreteMethod()
    assert isinstance(method, BaseMemoryMethod)
    assert isinstance(method, ABC)