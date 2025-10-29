from ..base import BaseModel
from langchain_ollama.llms import OllamaLLM

class OllamaModel(BaseModel):
    """Provides a connector to local Ollama"""
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.llm = OllamaLLM(model=model_name, **kwargs)
        
    async def generate(self, prompt, system=None, **kwargs):
        # if system prompt provided adds system prompt
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = await self.llm.ainvoke(full_prompt)
        
        return {
            'content' : response, 
            'metatdata' : self.get_model_info()
        }
        
    def get_model_info(self):
        return {'model': self.model_name, 'provider' : 'ollama'}