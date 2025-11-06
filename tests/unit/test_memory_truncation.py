"""
Tests for the TruncationMemory class.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_truncation_memory_basic_functionality():
    """Test basic truncation functionality."""
    from memory.methods.truncation_memory import TruncationMemory
    
    memory = TruncationMemory(max_tokens=5)
    
    text = "This is a long text that should be truncated"
    result = memory.process(text)
    
    # Should be truncated to 5 tokens
    assert len(result.split()) == 5
    assert result == "This is a long text"


def test_truncation_memory_with_kwargs():
    """Test that max_tokens can be passed as kwargs to process method."""
    from memory.methods.truncation_memory import TruncationMemory
    
    memory = TruncationMemory(max_tokens=10)
    
    text = "This is a long text that should be truncated"
    
    # Override max_tokens in process call
    result = memory.process(text, max_tokens=3)
    assert len(result.split()) == 3
    assert result == "This is a"
    
    # Use default max_tokens - text has 9 tokens, so should return all 9
    result_default = memory.process(text)
    assert len(result_default.split()) == 9  # Fixed: text actually has 9 tokens
    assert result_default == text  # Should return unchanged since 9 < 10


def test_truncation_memory_no_truncation_needed():
    """Test when text is shorter than max_tokens."""
    from memory.methods.truncation_memory import TruncationMemory
    
    memory = TruncationMemory(max_tokens=100)
    
    text = "Short text"
    result = memory.process(text)
    
    assert result == text
    assert len(result.split()) == 2


def test_truncation_memory_empty_text():
    """Test truncation with empty text."""
    from memory.methods.truncation_memory import TruncationMemory
    
    memory = TruncationMemory(max_tokens=5)
    
    result = memory.process("")
    assert result == ""
    
    # Whitespace-only text should be handled according to actual split() behavior
    result = memory.process("   ")
    # split() on whitespace-only string returns empty list, so result should be empty
    assert result == ""


def test_truncation_memory_single_token():
    """Test truncation to single token."""
    from memory.methods.truncation_memory import TruncationMemory
    
    memory = TruncationMemory(max_tokens=1)
    
    text = "Multiple words here"
    result = memory.process(text)
    
    assert result == "Multiple"
    assert len(result.split()) == 1


def test_truncation_memory_get_method_info():
    """Test the get_method_info method."""
    from memory.methods.truncation_memory import TruncationMemory
    
    memory = TruncationMemory(max_tokens=50)
    info = memory.get_method_info()
    
    assert isinstance(info, dict)
    assert info["method"] == "truncation"
    assert "version" in info
    assert "parameters" in info
    assert "max_tokens" in info["parameters"]
    assert "description" in info


def test_truncation_memory_inheritance():
    """Test that TruncationMemory inherits from BaseMemory."""
    from memory.methods.truncation_memory import TruncationMemory
    from memory.BaseMemory import BaseMemory
    
    memory = TruncationMemory(max_tokens=10)
    assert isinstance(memory, BaseMemory)


def test_truncation_memory_initialization():
    """Test different initialization options."""
    from memory.methods.truncation_memory import TruncationMemory
    
    # Default initialization
    memory1 = TruncationMemory()
    assert hasattr(memory1, 'max_tokens')
    
    # With max_tokens parameter
    memory2 = TruncationMemory(max_tokens=25)
    assert memory2.max_tokens == 25
    
    # With additional kwargs
    memory3 = TruncationMemory(max_tokens=15, custom_param="value")
    assert memory3.max_tokens == 15


def test_truncation_memory_whitespace_handling():
    """Test that whitespace is handled correctly."""
    from memory.methods.truncation_memory import TruncationMemory
    
    memory = TruncationMemory(max_tokens=3)
    
    # Multiple spaces between words
    text = "Word1    Word2     Word3   Word4"
    result = memory.process(text)
    
    # Should still get first 3 tokens
    assert len(result.split()) == 3
    assert "Word1" in result
    assert "Word2" in result
    assert "Word3" in result


def test_truncation_memory_zero_tokens():
    """Test edge case with zero max_tokens."""
    from memory.methods.truncation_memory import TruncationMemory
    
    memory = TruncationMemory(max_tokens=0)
    
    text = "Some text here"
    result = memory.process(text)
    
    assert result == ""
