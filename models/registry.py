from typing import Dict, Type
from base import BaseModel
from providers.ollama import OllamaModel

class ModelRegistry:
    """Central registry for model discovery."""
    
    _providers : Dict[str, Type[BaseModel]] = {
        "ollama": OllamaModel,
    }
    
    @classmethod
    def create_model(cls, provider: str, model_name: str, **kwargs) -> BaseModel:
        """Factory method to create model instances based on provider and model name."""
        if provider not in cls._providers:
            raise ValueError(f"Provider '{provider}' is not registered.")
        
        return cls._providers[provider](model_name=model_name, **kwargs)
    
    @classmethod
    def register_provider(cls, name: str, provider_cls: Type[BaseModel]) -> None:
        """Register a new model provider."""
        cls._providers[name] = provider_cls