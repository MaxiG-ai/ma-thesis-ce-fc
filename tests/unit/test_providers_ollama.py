from models.providers.ollama import OllamaModel 
import ollama
import pytest

def test_instantiate_ollama_model():
    """Test that OllamaModel can be instantiated"""
    model = OllamaModel(model_name="gemma3")
    assert model.model_name == "gemma3"

def test_inherits_from_base_model():
    """Test that OllamaModel is a BaseModel instance."""
    from models.BaseModel import BaseModel
    
    model = OllamaModel(model_name="gemma3")
    assert isinstance(model, BaseModel)

def test_instantiate_with_different_model_names():
        """Test instantiation with various model names."""
        model_names = ["gemma3", "llama2", "mistral", "codellama"]
        
        for name in model_names:
            model = OllamaModel(model_name=name)
            assert model.model_name == name

@pytest.mark.asyncio
async def test_unsupported_model_raises_error():
    """Test that using an unsupported model raises an error."""
    # Get list of supported models
    supported_models = [model.model for model in ollama.list().models]
    
    # Use a model name that's definitely not supported
    unsupported_model = "definitely_not_a_real_model_name_12345"
    
    # Ensure our test model is actually unsupported
    assert unsupported_model not in supported_models
    
    # Test that instantiation raises an error
    with pytest.raises(TypeError):
        model = OllamaModel(model_name=unsupported_model)
        # Try to generate text to trigger the error
        await model.generate_text(prompt="Test")

# test that generation matches expected output for a known model
@pytest.mark.asyncio
async def test_generation_output_matches_expected():
    """Test that generation output matches expected structure for a known model."""
    supported_models = [model.model for model in ollama.list().models]
    assert len(supported_models) > 0, "No supported models found in Ollama."
    model = OllamaModel(model_name=supported_models[0])

    prompt = "Hello, how are you?"
    
    result = await model.generate_text(prompt=prompt)
    
    # Assert the structure matches expected format
    assert isinstance(result, dict), "Result should be a dictionary"
    assert 'message' in result, "Result should have 'message' key"
    assert len(result['message']) > 0, "Messages should not be empty"

