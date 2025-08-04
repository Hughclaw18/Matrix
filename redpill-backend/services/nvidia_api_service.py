from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings
import requests
from config.constants import LLM_MODEL, EMBEDDING_MODEL
from utils.common import get_nvidia_api_key

class NvidiaAPIService:
    def __init__(self):
        self.api_key = get_nvidia_api_key()
        self.llm = ChatNVIDIA(model=LLM_MODEL, nvidia_api_key=self.api_key)
        self.embeddings = NVIDIAEmbeddings(model=EMBEDDING_MODEL, nvidia_api_key=self.api_key)

    def get_llm_response(self, prompt: str):
        return self.llm.invoke(prompt)

    async def get_embedding(self, text: str):
        return await self.embeddings.aembed_query(text)

    async def perform_ocr(self, image_data_url: str):
        invoke_url = "https://ai.api.nvidia.com/v1/cv/baidu/paddleocr"
        payload = {"input": [{"type": "image_url", "url": image_data_url}]}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(invoke_url, headers=headers, json=payload)
            response.raise_for_status()
            print(f"OCR API Response Status: {response.status_code}")
            print(f"OCR API Response Content: {response.text}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error during OCR request: {e}")
            return None