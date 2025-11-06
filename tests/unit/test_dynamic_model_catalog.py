"""
tests/unit/test_dynamic_model_catalog.py
Test dynamic model catalog functionality in ModelRegistry.
"""

import pytest
from models.registry import ModelRegistry


def setup_function():
    """Reset the model catalog before each test."""
    ModelRegistry._provider_model_catalog = {}


def test_update_provider_catalog_basic():
    """Test basic catalog update from provider config."""
    providers_config = {
        "openrouter": {
            "models": ["google/gemma-3-27b-it:free", "gpt-4", "claude-3-sonnet"],
            "enabled_models": ["google/gemma-3-27b-it:free"],
            "temperature": 0.3
        },
        "ollama": {
            "models": ["llama3.2:3b", "gemma3:270m"],
            "enabled_models": ["llama3.2:3b"],
            "temperature": 0.3
        }
    }
    
    ModelRegistry.update_provider_catalog(providers_config)
    
    # Check that catalog was updated
    assert "openrouter" in ModelRegistry._provider_model_catalog
    assert "ollama" in ModelRegistry._provider_model_catalog
    
    # Check models were loaded correctly
    openrouter_models = ModelRegistry.get_provider_models("openrouter")
    assert "google/gemma-3-27b-it:free" in openrouter_models
    assert "gpt-4" in openrouter_models
    assert "claude-3-sonnet" in openrouter_models
    
    ollama_models = ModelRegistry.get_provider_models("ollama")
    assert "llama3.2:3b" in ollama_models
    assert "gemma3:270m" in ollama_models


def test_create_model_with_dynamic_catalog():
    """Test model creation uses dynamic catalog for validation."""
    providers_config = {
        "openrouter": {
            "models": ["google/gemma-3-27b-it:free"],
            "enabled_models": ["google/gemma-3-27b-it:free"]
        }
    }
    
    ModelRegistry.update_provider_catalog(providers_config)
    
    # Should not produce warning since model is in dynamic catalog
    model = ModelRegistry.create_model("openrouter", "google/gemma-3-27b-it:free")
    assert hasattr(model, 'model_name')
    assert model.model_name == "google/gemma-3-27b-it:free"


def test_empty_provider_config():
    """Test handling of empty provider config."""
    providers_config = {}
    
    ModelRegistry.update_provider_catalog(providers_config)
    
    # Should return empty list when no config and no models in catalog
    openrouter_models = ModelRegistry.get_provider_models("openrouter")
    assert openrouter_models == []


def test_invalid_provider_config():
    """Test handling of invalid provider config."""
    providers_config = {
        "openrouter": "invalid_config",  # Not a dict
        "ollama": {
            "models": ["llama3.2:3b"]
        }
    }
    
    ModelRegistry.update_provider_catalog(providers_config)
    
    # Should skip invalid config but process valid ones
    assert "openrouter" not in ModelRegistry._provider_model_catalog
    assert "ollama" in ModelRegistry._provider_model_catalog
    
    ollama_models = ModelRegistry.get_provider_models("ollama")
    assert "llama3.2:3b" in ollama_models


def test_unknown_model_without_catalog():
    """Test that unknown models produce warning when no catalog is loaded."""
    # Don't load any catalog
    
    # This should produce a warning but still create the model
    model = ModelRegistry.create_model("openrouter", "unknown-model")
    assert hasattr(model, 'model_name')
    assert model.model_name == "unknown-model"
