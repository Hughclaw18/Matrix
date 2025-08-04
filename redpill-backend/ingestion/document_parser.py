from docx import Document
from PIL import Image
import pytesseract
import io
import base64
from docx import Document
import aiofiles
from services.nvidia_api_service import NvidiaAPIService

class DocumentParser:
    def __init__(self):
        self.nvidia_api_service = NvidiaAPIService()

    def parse_pdf(self, file_path: str):
        # This is a placeholder. Full PDF parsing requires a library like PyPDF2 or pdfplumber.
        # For multimodal extraction, NeMo Retriever Extraction would be used.
        return "Parsed content from PDF (placeholder)"

    def parse_docx(self, file_path: str):
        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return "\n".join(full_text)

    async def extract_text_from_image(self, image_path: str):
        try:
            # Convert image to base64 data URL
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Determine image type for data URL
            image_type = Image.open(image_path).format.lower()
            if image_type == 'jpeg':
                image_type = 'jpg'
            image_data_url = f"data:image/{image_type};base64,{encoded_string}"

            # Perform OCR using NVIDIA NIM
            ocr_result = await self.nvidia_api_service.perform_ocr(image_data_url)
            if ocr_result and 'output' in ocr_result and ocr_result['output']:
                # Assuming the OCR result structure has 'output' -> 'text' or similar
                # You might need to adjust this based on the actual NIM OCR output format
                extracted_text = ""
                for item in ocr_result['output']:
                    if 'text' in item:
                        extracted_text += item['text'] + "\n"
                return extracted_text.strip()
            else:
                return "No text extracted or OCR service failed."
        except Exception as e:
            return f"Error during NVIDIA OCR: {e}"

    def parse_audio(self, file_path: str):
        # This is a placeholder. Full audio parsing requires a library like SpeechRecognition and pydub.
        # For ASR, Riva ASR would be used.
        return "Parsed content from audio (placeholder)"

    async def parse_txt(self, file_path: str):
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
            return await f.read()