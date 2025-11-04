"""
Unified registry for all evaluation components.
"""

from typing import Dict, Type, List, Any
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.registry import ModelRegistry
from memory.registry import MemoryRegistry
from evaluation.BenchmarkAdapter import BenchmarkAdapter


class BenchmarkRegistry:
    """Registry for benchmark adapters."""
    
    _benchmarks: Dict[str, Type[BenchmarkAdapter]] = {}
    
    @classmethod
    def create_benchmark(cls, benchmark_name: str, **kwargs) -> BenchmarkAdapter:
        """Create benchmark instance."""
        if benchmark_name not in cls._benchmarks:
            raise ValueError(f"Benchmark '{benchmark_name}' not registered")
        
        return cls._benchmarks[benchmark_name](**kwargs)
    
    @classmethod
    def register_benchmark(cls, name: str, benchmark_cls: Type[BenchmarkAdapter]) -> None:
        """Register a new benchmark."""
        cls._benchmarks[name] = benchmark_cls
    
    @classmethod
    def get_available_benchmarks(cls) -> List[str]:
        """Get available benchmark names."""
        return list(cls._benchmarks.keys())


class ComponentRegistry:
    """Unified registry for all evaluation components."""
    
    @classmethod
    def create_model(cls, provider: str, model_name: str, **kwargs):
        """Create model instance."""
        return ModelRegistry.create_model(provider, model_name, **kwargs)
    
    @classmethod
    def create_memory_method(cls, method_name: str, **kwargs):
        """Create memory method instance."""
        return MemoryRegistry.create_method(method_name, **kwargs)
    
    @classmethod
    def create_benchmark(cls, benchmark_name: str, **kwargs):
        """Create benchmark instance."""
        return BenchmarkRegistry.create_benchmark(benchmark_name, **kwargs)
    
    @classmethod
    def register_model(cls, name: str, model_cls):
        """Register a new model provider."""
        ModelRegistry.register_provider(name, model_cls)
    
    @classmethod
    def register_memory_method(cls, name: str, method_cls):
        """Register a new memory method."""
        MemoryRegistry.register_method(name, method_cls)
    
    @classmethod
    def register_benchmark(cls, name: str, benchmark_cls):
        """Register a new benchmark."""
        BenchmarkRegistry.register_benchmark(name, benchmark_cls)
    
    @classmethod
    def get_available_components(cls) -> Dict[str, List[str]]:
        """Get all available components."""
        return {
            "models": ModelRegistry.get_available_providers(),
            "memory_methods": MemoryRegistry.get_available_methods(),
            "benchmarks": BenchmarkRegistry.get_available_benchmarks()
        }
    
    @classmethod
    def get_model_info(cls, provider: str, model_name: str) -> Dict[str, Any]:
        """Get model information."""
        model = cls.create_model(provider, model_name)
        return model.get_model_info()
    
    @classmethod
    def get_memory_method_info(cls, method_name: str) -> Dict[str, Any]:
        """Get memory method information."""
        return MemoryRegistry.get_method_info(method_name)