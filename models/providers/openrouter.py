import openai
from typing import Dict, Any, cast
from ..BaseModel import BaseModel

import os 
from dotenv import load_dotenv

load_dotenv()

class OpenRouterModel(BaseModel): #TODO: Properly implement OpenRouterModel class
    """Provides a connector to local OpenRouter"""
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.base_url = "https://openrouter.ai/api/v1"

    def chatresponse_to_dict(self, response):
        """Convert ChatResponse object to dictionary format"""
        return {
            'model': response.model,
            'created_at': response.created,
            # 'done': response.done,
            'done_reason': response.choices[0].finish_reason,
            # 'total_duration': response.total_duration,
            # 'load_duration': response.load_duration,
            # 'prompt_eval_count': response.prompt_eval_count,
            # 'prompt_eval_duration': response.prompt_eval_duration,
            # 'eval_count': response.eval_count,
            # 'eval_duration': response.eval_duration,
            'message': {
                'role': response.choices[0].message.role,
                'content': response.choices[0].message.content,
                # 'thinking': response.choices[0].message.thinking,
                # 'images': response.choices[0].message.images,
                # 'tool_name': response.choices[0].message.tool_name if response.choices[0].message.tool_name else None,
                # 'tool_calls': response.choices[0].message.tool_calls if response.choices[0].message.tool_calls else None
            }
        }

    async def generate_text(self, prompt, system=None, **kwargs) -> Dict[str, Any]:

        client = self._generate_client()

        if system:
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ]
        else:
            messages = [
                {"role": "user", "content": prompt}
            ]

        # Cast messages to Any to satisfy the typed signature of the client API
        completion = client.chat.completions.create(
            model=self.model_name,
            messages=cast(Any, messages)
        )

        return self.chatresponse_to_dict(completion)

    def _generate_client(self):

        client = openai.OpenAI(
            base_url=self.get_base_url(),
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
    
        return client
        
    def get_model_info(self):
        return {'model': self.model_name, 'provider' : 'openrouter'}

    def get_base_url(self) -> str:
        return self.base_url