from rag.rag_pipeline import RAGPipeline

class ChatHandler:
    def __init__(self):
        self.rag_pipeline = RAGPipeline()

    async def process_message(self, message: str):
        response = await self.rag_pipeline.run_pipeline(message)
        return response