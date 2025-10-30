import ollama
from ..base import BaseModel

class OllamaModel(BaseModel):
    """Provides a connector to local Ollama"""
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        # TODO: Evaluate if it can be replaced by ollama module directly

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

    async def generate_text(self, prompt, system=None, **kwargs):
        # if system prompt provided adds system prompt
        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        # get the response from the model using ollama
        try:
            response = ollama.chat(model=self.model_name, messages=[
                {
                    'role': 'user',
                    'content': full_prompt,
                },
            ])

            return self.chatresponse_to_dict(response)

        except ollama.ResponseError as e:
            raise TypeError(f"Ollama model error: {str(e)}") from e
        
    async def get_model_info(self):
        return {'model': self.model_name, 'provider' : 'ollama'}