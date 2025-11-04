"""
Truncation-based memory management method.
"""

from typing import Dict, Any
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from memory.base import BaseMemoryMethod


class TruncationMemory(BaseMemoryMethod):
    """Memory method that truncates text to fit within token limits."""
    
    def __init__(self, max_tokens: int = 500, **kwargs):
        """
        Initialize truncation memory method.
        
        Args:
            max_tokens: Maximum number of tokens to keep
            **kwargs: Additional configuration parameters
        """
        self.max_tokens = max_tokens
        self.config = kwargs
    
    def process(self, text: str, **kwargs) -> str:
        """
        Truncate the input text to fit within the specified maximum token limit.
        
        Args:
            text: The input text to be truncated
            **kwargs: Runtime parameters, including optional 'max_tokens' override
            
        Returns:
            The truncated text
        """
        # Use runtime max_tokens if provided, otherwise use instance default
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        
        # Simple whitespace-based tokenization (for demonstration purposes)
        tokens = text.split()
        
        # If no tokens (empty or whitespace-only), return empty string
        if not tokens:
            return ""
        
        if len(tokens) <= max_tokens:
            return text
        
        # Truncate tokens to max_tokens
        truncated_tokens = tokens[:max_tokens]
        
        # Join tokens back into a string
        truncated_text = ' '.join(truncated_tokens)
        
        return truncated_text
    
    def get_method_info(self) -> Dict[str, Any]:
        """Return information about this memory method."""
        return {
            "method": "truncation",
            "version": "1.0.0",
            "description": "Truncates text to a maximum number of tokens using whitespace-based tokenization",
            "parameters": ["max_tokens"],
            "default_max_tokens": self.max_tokens,
            "config": self.config
        }


# Backward compatibility function
def truncate_memory(text: str, max_tokens: int) -> str:
    """
    Legacy function interface for backward compatibility.
    
    Args:
        text: The input text to be truncated
        max_tokens: The maximum number of tokens allowed
        
    Returns:
        The truncated text
    """
    method = TruncationMemory(max_tokens=max_tokens)
    return method.process(text)