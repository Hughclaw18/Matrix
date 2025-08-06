import os
import os
import google.generativeai as genai
from langchain.prompts import PromptTemplate
from config.constants import PERSONA_PROMPT_TEMPLATE, LLM_MODEL_NAME

class GoogleChatService:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(LLM_MODEL_NAME)
        self.prompt_template = PromptTemplate.from_template(PERSONA_PROMPT_TEMPLATE)

    def get_chat_response(self, context: str, question: str):
        formatted_prompt = self.prompt_template.format(context=context, question=question)
        
        completion = self.model.generate_content(
            formatted_prompt,
            generation_config=genai.types.GenerationConfig(
                candidate_count=1,
                max_output_tokens=4096,
                temperature=0.6,
                top_p=0.7
            ),
            stream=True
        )

        full_response_content = ""
        for chunk in completion:
            full_response_content += chunk.text
        return full_response_content