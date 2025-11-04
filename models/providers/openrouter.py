import openrouter
from typing import Dict, Any
from ..base import BaseModel

class OpenRouterModel(BaseModel): #TODO: Properly implement OpenRouterModel class
    """Provides a connector to local OpenRouter"""
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name

    def chatresponse_to_dict(self, response):
        """Convert ChatResponse object to dictionary format"""
        return {
            'model': response.model,
            'created_at': response.created_at,
            'done': response.done,
            'done_reason': response.done_reason,
            'total_duration': response.total_duration,
            'load_duration': response.load_duration,
            'prompt_eval_count': response.prompt_eval_count,
            'prompt_eval_duration': response.prompt_eval_duration,
            'eval_count': response.eval_count,
            'eval_duration': response.eval_duration,
            'message': {
                'role': response.message.role,
                'content': response.message.content,
                'thinking': response.message.thinking,
                'images': response.message.images,
                'tool_name': response.message.tool_name,
                'tool_calls': response.message.tool_calls
            }
        }

    async def generate_text(self, prompt, system=None, **kwargs) -> Dict[str, Any]:
        return dict()
        
    def get_model_info(self):
        return {'model': self.model_name, 'provider' : 'openrouter'}