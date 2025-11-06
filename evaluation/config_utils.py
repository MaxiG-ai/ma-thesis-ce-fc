"""Configuration utilities for provider-specific model management."""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

def validate_provider_config(config: Dict[str, Any]) -> None:
    """Validate provider configuration structure."""
    providers = config.get("providers", {})
    
    if not providers:
        raise ValueError("No providers configured")
    
    for provider_name, provider_config in providers.items():
        if not isinstance(provider_config, dict):
            raise ValueError(f"Provider '{provider_name}' config must be a dictionary")
        
        # Check required fields
        if "models" not in provider_config:
            raise ValueError(f"Provider '{provider_name}' missing 'models' list")
        
        if "enabled_models" not in provider_config:
            logger.warning(f"Provider '{provider_name}' missing 'enabled_models', defaulting to empty")
            provider_config["enabled_models"] = []

def get_enabled_models_summary(config: Dict[str, Any]) -> Dict[str, List[str]]:
    """Get summary of enabled models by provider."""
    summary = {}
    
    for provider_name, provider_config in config.get("providers", {}).items():
        enabled = provider_config.get("enabled_models", [])
        if enabled:
            summary[provider_name] = enabled
    
    return summary

def get_total_enabled_models(config: Dict[str, Any]) -> int:
    """Get total count of enabled models."""
    total = 0
    for provider_config in config.get("providers", {}).values():
        total += len(provider_config.get("enabled_models", []))
    return total

def disable_model(config: Dict[str, Any], provider: str, model: str) -> bool:
    """Disable a specific model. Returns True if model was found and disabled."""
    provider_config = config.get("providers", {}).get(provider)
    if not provider_config:
        return False
    
    enabled_models = provider_config.get("enabled_models", [])
    if model in enabled_models:
        enabled_models.remove(model)
        return True
    return False

def enable_model(config: Dict[str, Any], provider: str, model: str) -> bool:
    """Enable a specific model. Returns True if model was found and enabled."""
    provider_config = config.get("providers", {}).get(provider)
    if not provider_config:
        return False
    
    available_models = provider_config.get("models", [])
    if model not in available_models:
        return False
    
    enabled_models = provider_config.get("enabled_models", [])
    if model not in enabled_models:
        enabled_models.append(model)
        return True
    return False

def get_available_models_by_provider(config: Dict[str, Any]) -> Dict[str, List[str]]:
    """Get all available models organized by provider."""
    available = {}
    
    for provider_name, provider_config in config.get("providers", {}).items():
        models = provider_config.get("models", [])
        if models:
            available[provider_name] = models
    
    return available

def get_provider_config_summary(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get comprehensive summary of provider configuration."""
    providers = config.get("providers", {})
    
    summary = {
        "total_providers": len(providers),
        "providers": {},
        "total_available_models": 0,
        "total_enabled_models": 0
    }
    
    for provider_name, provider_config in providers.items():
        available_models = provider_config.get("models", [])
        enabled_models = provider_config.get("enabled_models", [])
        
        provider_summary = {
            "available_models": len(available_models),
            "enabled_models": len(enabled_models),
            "models": available_models,
            "enabled": enabled_models,
            "settings": {
                k: v for k, v in provider_config.items() 
                if k not in ["models", "enabled_models"]
            }
        }
        
        summary["providers"][provider_name] = provider_summary
        summary["total_available_models"] += len(available_models)
        summary["total_enabled_models"] += len(enabled_models)
    
    return summary

def validate_enabled_models(config: Dict[str, Any]) -> List[str]:
    """Validate all enabled models are in their provider's available models list.
    
    Returns:
        List of validation errors (empty if all valid)
    """
    errors = []
    
    for provider_name, provider_config in config.get("providers", {}).items():
        available_models = set(provider_config.get("models", []))
        enabled_models = provider_config.get("enabled_models", [])
        
        invalid_models = set(enabled_models) - available_models
        if invalid_models:
            errors.append(
                f"Provider '{provider_name}' has invalid enabled models: {list(invalid_models)}. "
                f"Available models: {list(available_models)}"
            )
    
    return errors
