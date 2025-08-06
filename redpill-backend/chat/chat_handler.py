from services.google_chat_service import GoogleChatService

class ChatHandler:
    def __init__(self):
        self.google_chat_service = GoogleChatService()

    def process_message(self, context: str, question: str):
        response = self.google_chat_service.get_chat_response(context, question)
        return response