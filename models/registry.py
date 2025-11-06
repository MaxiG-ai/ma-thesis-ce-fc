from typing import Dict, Type, List, Any, Optional
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
    
    # Dynamic model catalog loaded from configuration
    _provider_model_catalog: Dict[str, List[str]] = {}
    
    @classmethod
    def create_model(cls, provider: str, model_name: str, **kwargs) -> BaseModel:
        """Factory method to create model instances with validation."""
        if provider not in cls._providers:
            available = list(cls._providers.keys())
            raise ValueError(f"Provider '{provider}' is not registered. Available: {available}")
        
        # Validate model is known using dynamic catalog
        known_models = cls._get_provider_models_for_validation(provider)
        if known_models and model_name not in known_models:
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
    def _get_provider_models_for_validation(cls, provider: str) -> List[str]:
        """Get provider models for validation purposes."""
        return cls._provider_model_catalog.get(provider, [])
    
    @classmethod
    def update_provider_catalog(cls, providers_config: Dict[str, Dict[str, Any]]) -> None:
        """Update the model catalog from provider configuration."""
        logger.info("Updating model catalog from configuration...")
        
        for provider_name, provider_config in providers_config.items():
            if not isinstance(provider_config, dict):
                continue
            
            # Extract models from provider config
            models = provider_config.get("models", [])
            if models:
                cls._provider_model_catalog[provider_name] = models
                logger.info(f"Updated catalog for provider '{provider_name}': {len(models)} models")
        
        logger.info(f"Model catalog updated for {len(cls._provider_model_catalog)} providers")
    
    @classmethod
    def validate_provider_config(cls, provider_config: Dict[str, Any]) -> None:
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
