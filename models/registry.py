from typing import Dict, Type, List, Any
import logging
from .BaseModel import BaseModel
from .providers.ollama import OllamaModel
from .providers.openrouter import OpenRouterModel

logger = logging.getLogger(__name__)

class ModelRegistry:
    """Central registry for model discovery."""
    
    _providers: Dict[str, Type[BaseModel]] = {
        "ollama": OllamaModel,
        "openrouter": OpenRouterModel,
    }
    
    # Model catalog for validation (optional but recommended)
    _provider_model_catalog = {
        "ollama": [
            "llama3.2:3b", "llama3.1:8b", "llama3.1:70b",
            "gemma3:270m", "mistral:7b", "qwen2.5:7b"
        ],
        "openrouter": [
            "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", 
            "claude-3-sonnet", "claude-3-haiku"
        ],
        "anthropic": [
            "claude-3-sonnet-20240229", "claude-3-haiku-20240307"
        ]
    }
    
    @classmethod
    def create_model(cls, provider: str, model_name: str, **kwargs) -> BaseModel:
        """Factory method to create model instances with validation."""
        if provider not in cls._providers:
            available = list(cls._providers.keys())
            raise ValueError(f"Provider '{provider}' is not registered. Available: {available}")
        
        # Optional: Validate model is known (can be disabled for flexibility)
        if provider in cls._provider_model_catalog:
            known_models = cls._provider_model_catalog[provider]
            if model_name not in known_models:
                logger.warning(f"Model '{model_name}' not in catalog for provider '{provider}'. "
                             f"Known models: {known_models}")
        
        return cls._providers[provider](model_name=model_name, **kwargs)
    
    @classmethod
    def register_provider(cls, name: str, provider_cls: Type[BaseModel]) -> None:
        """Register a new model provider."""
        cls._providers[name] = provider_cls
        logger.info(f"Registered provider: {name}")
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available model provider names."""
        return list(cls._providers.keys())
    
    @classmethod
    def get_provider_models(cls, provider: str) -> List[str]:
        """Get known models for a provider."""
        return cls._provider_model_catalog.get(provider, [])
    
    @classmethod
    def get_all_provider_models(cls) -> Dict[str, List[str]]:
        """Get all known models by provider."""
        return cls._provider_model_catalog.copy()
    
    @classmethod
    def validate_provider_config(cls, provider_config: Dict[str, any]) -> None:
        """Validate provider configuration structure."""
        for provider_name, config in provider_config.items():
            if provider_name not in cls._providers:
                logger.warning(f"Provider '{provider_name}' is configured but not registered")
            
            if not isinstance(config, dict):
                raise ValueError(f"Provider '{provider_name}' config must be a dictionary")
            
            if "models" not in config:
                raise ValueError(f"Provider '{provider_name}' missing required 'models' list")
            
            if "enabled_models" not in config:
                logger.info(f"Provider '{provider_name}' missing 'enabled_models', defaulting to empty")
