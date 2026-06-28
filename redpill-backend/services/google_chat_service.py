import os
from google import genai
from google.genai import types
from langchain_core.prompts import PromptTemplate
from config.constants import PERSONA_PROMPT_TEMPLATE, LLM_MODEL_NAME

class GoogleChatService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key else None
        
        # Clean up model name format for the new SDK
        self.model_name = LLM_MODEL_NAME
        if LLM_MODEL_NAME.startswith("models/"):
            self.model_name = LLM_MODEL_NAME.replace("models/", "")
            
        self.prompt_template = PromptTemplate.from_template(PERSONA_PROMPT_TEMPLATE)

    def get_chat_response(self, context: str, question: str):
        if not self.client:
            return "Google API Key not configured."
            
        formatted_prompt = self.prompt_template.format(context=context, question=question)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=formatted_prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=4096,
                    temperature=0.6,
                    top_p=0.7
                )
            )
            return response.text
        except Exception as e:
            return f"Gemini API Error: {str(e)}"