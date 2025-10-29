# tests/unit/test_base_model.py
import pytest
from models.base import BaseModel


class MockModel(BaseModel):
    """Concrete implementation for testing"""

    async def generate_text(self, prompt: str, system=None, **kwargs):
        return {
            "content": "test response",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            "metadata": {"model": "mock", "provider": "test"},
        }

    def get_model_info(self):
        return {"name": "mock", "provider": "test"}


@pytest.mark.asyncio
async def test_base_model_has_generate_method():
    """Test that BaseModel requires generate method"""
    model = MockModel()
    response = await model.generate_text("test prompt")

    assert "content" in response
    assert "usage" in response
    assert "metadata" in response


def test_base_model_has_get_model_info():
    """Test that BaseModel requires get_model_info method"""
    model = MockModel()
    info = model.get_model_info()

    assert "name" in info
    assert "provider" in info


def test_cannot_instantiate_base_model():
    """Test that BaseModel is abstract and cannot be instantiated"""
    with pytest.raises(TypeError):
        BaseModel()
