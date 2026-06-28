from services.llm_service import LLMService

class ChatHandler:
    def __init__(self):
        self.llm_service = LLMService()

    def process_message(self, provider: str, model_name: str, context: str, question: str):
        response = self.llm_service.get_chat_response(provider, model_name, context, question)
        return response