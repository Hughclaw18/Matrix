import os
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from config.constants import LLM_MODEL
from utils.common import get_nvidia_api_key

class NvidiaChatService:
    def __init__(self):
        self.api_key = get_nvidia_api_key()
        self.llm = ChatNVIDIA(model=LLM_MODEL, nvidia_api_key=self.api_key)

    def get_chat_response(self, message: str):
        return self.llm.invoke(message)