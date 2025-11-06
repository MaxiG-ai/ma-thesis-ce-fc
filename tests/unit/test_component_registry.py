"""
Tests for the ComponentRegistry unified class.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_component_registry_get_available_components():
    """Test getting available components."""
    from evaluation.registries import ComponentRegistry
    
    components = ComponentRegistry.get_available_components()
    
    assert isinstance(components, dict)
    assert "models" in components
    assert "memory_methods" in components
    assert "benchmarks" in components
    
    assert isinstance(components["models"], list)
    assert isinstance(components["memory_methods"], list)
    assert isinstance(components["benchmarks"], list)
    
    # Should have default components
    assert "ollama" in components["models"]
    assert "truncation" in components["memory_methods"]


def test_component_registry_create_model():
    """Test creating model instances through ComponentRegistry."""
    from evaluation.registries import ComponentRegistry
    from models.BaseModel import BaseModel
    
    model = ComponentRegistry.create_model("ollama", "test-model")
    
    assert isinstance(model, BaseModel)
    # Note: can't test model_name attribute as it's not in BaseModel interface


def test_component_registry_create_memory_method():
    """Test creating memory method instances through ComponentRegistry."""
    from evaluation.registries import ComponentRegistry
    from memory.BaseMemory import BaseMemory
    
    memory = ComponentRegistry.create_memory_method("truncation", max_tokens=100)
    
    assert isinstance(memory, BaseMemory)
    # Note: can't test max_tokens as it's not in BaseMemory interface


def test_component_registry_unknown_model():
    """Test error handling for unknown model providers."""
    from evaluation.registries import ComponentRegistry
    import pytest
    
    with pytest.raises(ValueError, match="Provider 'unknown' is not registered"):
        ComponentRegistry.create_model("unknown", "test-model")


def test_component_registry_unknown_memory_method():
    """Test error handling for unknown memory methods."""
    from evaluation.registries import ComponentRegistry
    import pytest
    
    with pytest.raises(ValueError, match="Memory method 'unknown' not registered"):
        ComponentRegistry.create_memory_method("unknown")


def test_component_registry_memory_method_info():
    """Test getting memory method information."""
    from evaluation.registries import ComponentRegistry
    
    info = ComponentRegistry.get_memory_method_info("truncation")
    
    assert isinstance(info, dict)
    assert info["method"] == "truncation"
    assert "version" in info


def test_component_registry_register_new_components():
    """Test registering new components."""
    from evaluation.registries import ComponentRegistry
    from models.BaseModel import BaseModel
    from memory.BaseMemory import BaseMemory
    
    # Create mock classes
    class TestModel(BaseModel):
        def __init__(self, model_name: str, **kwargs):
            self.model_name = model_name
        
        async def generate_text(self, prompt: str, system=None, **kwargs):
            return {"message": {"content": "test response"}}
        
        def get_model_info(self):
            return {"model": "test", "provider": "test"}
    
    class TestMemory(BaseMemory):
        def process(self, text: str, **kwargs) -> str:
            return f"test: {text}"
        
        def get_method_info(self):
            return {"method": "test", "version": "1.0"}
    
    # Register new components
    ComponentRegistry.register_model("test_model", TestModel)
    ComponentRegistry.register_memory_method("test_memory", TestMemory)
    
    # Test they are available
    components = ComponentRegistry.get_available_components()
    assert "test_model" in components["models"]
    assert "test_memory" in components["memory_methods"]
    
    # Test creation
    model = ComponentRegistry.create_model("test_model", "test")
    memory = ComponentRegistry.create_memory_method("test_memory")
    
    assert isinstance(model, TestModel)
    assert isinstance(memory, TestMemory)