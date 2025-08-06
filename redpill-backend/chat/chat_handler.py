from services.nvidia_chat_service import NvidiaChatService

class ChatHandler:
    def __init__(self):
        self.nvidia_chat_service = NvidiaChatService()

    async def process_message(self, message: str):
        response = self.nvidia_chat_service.get_chat_response(message)
        return response