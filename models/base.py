from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseModel(ABC):
    """Abstract base class for all LLM providers."""
    
    @abstractmethod
    async def generate_text(
        self, 
        prompt: str,
        system: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate response from LLM.

        Returns:
            {
                'content': str,
                'usage': {'prompt_tokens': int, 'completion_tokens': int},
                'metadata': {...}
            }
        """
        pass
    
    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """Return model name, provider, version"""
        pass
    