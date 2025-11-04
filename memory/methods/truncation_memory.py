def truncate_memory(text: str, max_tokens: int) -> str:
    """
    Truncate the input text to fit within the specified maximum token limit.
    
    Args:
        text (str): The input text to be truncated.
        max_tokens (int): The maximum number of tokens allowed.
        
    Returns:
        str: The truncated text.
    """
    # Simple whitespace-based tokenization (for demonstration purposes)
    tokens = text.split()
    
    if len(tokens) <= max_tokens:
        return text
    
    # Truncate tokens to max_tokens
    truncated_tokens = tokens[:max_tokens]
    
    # Join tokens back into a string
    truncated_text = ' '.join(truncated_tokens)
    
    return truncated_text