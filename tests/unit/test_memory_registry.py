"""
Tests for the MemoryRegistry class.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_memory_registry_has_default_providers():
    """Test that MemoryRegistry has default memory methods registered."""
    from memory.registry import MemoryRegistry
    
    # Should have truncation method by default
    available = MemoryRegistry.get_available_methods()
    assert "truncation" in available
    assert isinstance(available, list)


def test_memory_registry_create_method():
    """Test creating memory method instances."""
    from memory.registry import MemoryRegistry
    from memory.BaseMemory import BaseMemory
    
    # Create truncation method
    method = MemoryRegistry.create_method("truncation", max_tokens=50)
    
    assert isinstance(method, BaseMemory)
    assert method.max_tokens == 50


def test_memory_registry_create_method_with_kwargs():
    """Test creating memory methods with additional kwargs."""
    from memory.registry import MemoryRegistry
    
    method = MemoryRegistry.create_method(
        "truncation", 
        max_tokens=100, 
        custom_param="value"
    )
    
    assert method.max_tokens == 100
    assert method.config.get("custom_param") == "value"


def test_memory_registry_unknown_method():
    """Test error handling for unknown memory methods."""
    from memory.registry import MemoryRegistry
    
    import pytest
    with pytest.raises(ValueError, match="Memory method 'unknown' not registered"):
        MemoryRegistry.create_method("unknown")


def test_memory_registry_register_new_method():
    """Test registering a new memory method."""
    from memory.registry import MemoryRegistry
    from memory.BaseMemory import BaseMemory
    
    # Create a custom memory method
    class CustomMemoryMethod(BaseMemory):
        def __init__(self, **kwargs):
            self.config = kwargs
        
        def process(self, text: str, **kwargs) -> str:
            return f"custom: {text}"
        
        def get_method_info(self):
            return {"method": "custom", "version": "1.0"}
    
    # Register the new method
    MemoryRegistry.register_method("custom", CustomMemoryMethod)
    
    # Should now be available
    available = MemoryRegistry.get_available_methods()
    assert "custom" in available
    
    # Should be able to create instance
    method = MemoryRegistry.create_method("custom", param="value")
    assert isinstance(method, BaseMemory)
    assert method.config.get("param") == "value"
    
    # Test processing
    result = method.process("test")
    assert result == "custom: test"


def test_memory_registry_get_method_info():
    """Test getting information about registered methods."""
    from memory.registry import MemoryRegistry
    
    info = MemoryRegistry.get_method_info("truncation")
    
    assert isinstance(info, dict)
    assert info["method"] == "truncation"
    assert "version" in info
    assert "parameters" in info


def test_memory_registry_get_method_info_unknown():
    """Test getting info for unknown method."""
    from memory.registry import MemoryRegistry
    
    import pytest
    with pytest.raises(ValueError, match="Memory method 'unknown' not registered"):
        MemoryRegistry.get_method_info("unknown")


def test_memory_registry_list_all_methods():
    """Test listing all available methods with their info."""
    from memory.registry import MemoryRegistry
    
    all_methods = MemoryRegistry.list_all_methods()
    
    assert isinstance(all_methods, dict)
    assert "truncation" in all_methods
    assert isinstance(all_methods["truncation"], dict)
    assert all_methods["truncation"]["method"] == "truncation"


def test_memory_registry_inheritance():
    """Test that registry follows proper patterns."""
    from memory.registry import MemoryRegistry
    
    # Should have class methods
    assert hasattr(MemoryRegistry, 'create_method')
    assert hasattr(MemoryRegistry, 'register_method')
    assert hasattr(MemoryRegistry, 'get_available_methods')
    
    # Methods should be classmethods
    assert callable(getattr(MemoryRegistry, 'create_method'))
    assert callable(getattr(MemoryRegistry, 'register_method'))
    assert callable(getattr(MemoryRegistry, 'get_available_methods'))