"""
Registry imports for evaluation components.

This module provides easy access to individual component registries.
The ComponentRegistry has been removed to eliminate redundancy.
"""

# Import individual registries for direct use
from models.registry import ModelRegistry
from memory.registry import MemoryRegistry

# Note: BenchmarkRegistry is now defined in orchestrator.py to avoid circular imports
# This is because benchmark adapters need to import orchestrator functionality

__all__ = [
    "ModelRegistry",
    "MemoryRegistry",
]
