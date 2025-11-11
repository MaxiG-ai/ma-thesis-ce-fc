import os
import tomllib
from pathlib import Path
from typing import Dict, Type, List, Any, Optional
import logging
from .BaseModel import BaseModel
from .providers.ollama import OllamaModel
from .providers.openrouter import OpenRouterModel

logger = logging.getLogger(__name__)


class ModelConfig:
    """Configuration container for a specific model (local copy for compatibility)."""
    
    def __init__(self, name: str, provider_type: str, **kwargs: Any) -> None:
        """Initialize model configuration.
        
        Args:
            name: Model name identifier
            provider_type: Type of provider ('azure', 'openai', etc.)
            **kwargs: Additional configuration parameters
        """
        self.name: str = name
        self.provider_type: str = provider_type
        self.config: Dict[str, Any] = kwargs

class ModelRegistry:
    """Central registry for model discovery."""
    
    _providers: Dict[str, Type[BaseModel]] = {
        "ollama": OllamaModel,
        "openrouter": OpenRouterModel,
    }
    
    # Dynamic model catalog loaded from configuration
    _provider_model_catalog: Dict[str, List[str]] = {}
    
    # Provider settings loaded from configuration
    _provider_settings: Dict[str, Dict[str, Any]] = {}
    
    # Configuration loaded flag
    _config_loaded: bool = False
    
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
    def load_from_config(cls, config_path: str = "evaluation/config.toml") -> None:
        """Load configuration from TOML file and update model catalog."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        try:
            with open(config_file, "rb") as f:
                config = tomllib.load(f)
            
            providers_config = config.get("providers", {})
            if not providers_config:
                logger.warning("No providers configured in config file")
                return
            
            cls._update_catalog_and_settings(providers_config)
            cls._config_loaded = True
            logger.info(f"Configuration loaded from {config_path}")
            
        except Exception as e:
            raise ValueError(f"Failed to load config from {config_path}: {e}")
    
    @classmethod
    def _update_catalog_and_settings(cls, providers_config: Dict[str, Dict[str, Any]]) -> None:
        """Update the model catalog and provider settings from configuration."""
        logger.info("Updating model catalog and settings from configuration...")
        
        for provider_name, provider_config in providers_config.items():
            if not isinstance(provider_config, dict):
                continue
            
            # Extract models from provider config
            models = provider_config.get("models", [])
            if models:
                cls._provider_model_catalog[provider_name] = models
                logger.info(f"Updated catalog for provider '{provider_name}': {len(models)} models")
            
            # Store provider settings (exclude model lists)
            settings = {
                k: v for k, v in provider_config.items() 
                if k not in ["models", "enabled_models"]
            }
            if settings:
                cls._provider_settings[provider_name] = settings
                logger.info(f"Stored settings for provider '{provider_name}': {list(settings.keys())}")
        
        logger.info(f"Model catalog updated for {len(cls._provider_model_catalog)} providers")

    @classmethod
    def update_provider_catalog(cls, providers_config: Dict[str, Dict[str, Any]]) -> None:
        """Update the model catalog from provider configuration (legacy method)."""
        cls._update_catalog_and_settings(providers_config)
    
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

    @classmethod
    def get_provider_settings(cls, provider_name: str) -> Dict[str, Any]:
        """Get provider-specific settings from configuration."""
        if not cls._config_loaded:
            logger.warning("Configuration not loaded. Call load_from_config() first.")
            return {}
        
        return cls._provider_settings.get(provider_name, {})
    
    @classmethod
    def get_enabled_models(cls) -> Dict[str, List[str]]:
        """Get enabled models by provider from configuration."""
        if not cls._config_loaded:
            logger.warning("Configuration not loaded. Call load_from_config() first.")
            return {}
        
        # This would need the full config, but for now return all models
        # In the future, this should filter by enabled_models from config
        return cls._provider_model_catalog.copy()
    
    @classmethod
    def get_model_configs(cls) -> Dict[str, ModelConfig]:
        """Returns model configs in LLMFactory format for backward compatibility."""
        if not cls._config_loaded:
            logger.warning("Configuration not loaded. Call load_from_config() first.")
            return {}
        
        configs: Dict[str, ModelConfig] = {}
        
        for provider_name, models in cls._provider_model_catalog.items():
            if provider_name not in cls._providers:
                logger.warning(f"Provider '{provider_name}' not registered, skipping models: {models}")
                continue
            
            for model_name in models:
                # Create ModelConfig based on provider type
                if provider_name == "openrouter":
                    configs[model_name] = ModelConfig(
                        name=model_name,
                        provider_type="openrouter",
                        api_key=os.getenv("OPENROUTER_API_KEY"),
                        base_url="https://openrouter.ai/api/v1",
                        model_name=model_name
                    )
                elif provider_name == "ollama":
                    configs[model_name] = ModelConfig(
                        name=model_name,
                        provider_type="openai_compatible",
                        api_key=None,
                        base_url="http://localhost:11434/v1",
                        model_name=model_name
                    )
                else:
                    # Generic openai_compatible provider - use default base URL
                    configs[model_name] = ModelConfig(
                        name=model_name,
                        provider_type="openai_compatible",
                        api_key=None,  # Let provider handle API key
                        base_url=None,  # Provider will handle base URL
                        model_name=model_name
                    )
        
        logger.info(f"Generated {len(configs)} model configurations for LLMFactory compatibility")
        return configs
