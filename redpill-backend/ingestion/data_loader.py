from ingestion.document_parser import DocumentParser
from services.nvidia_api_service import NvidiaAPIService
from services.qdrant_service import QdrantService
from langchain.text_splitter import RecursiveCharacterTextSplitter

class DataLoader:
    def __init__(self):
        self.parser = DocumentParser()
        self.nvidia_service = NvidiaAPIService()
        self.qdrant_service = QdrantService()
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    async def ingest_document(self, file_path: str):
        content = ""
        import os
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == ".pdf":
            content = self.parser.parse_pdf(file_path)
        elif file_extension == ".docx":
            content = self.parser.parse_docx(file_path)
        elif file_extension == ".png" or file_extension == ".jpg" or file_extension == ".jpeg":
            content = await self.parser.extract_text_from_image(file_path)
        elif file_extension == ".mp3" or file_extension == ".wav":
            content = self.parser.parse_audio(file_path)
        elif file_extension == ".txt":
            content = await self.parser.parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

        chunks = self.text_splitter.split_text(content)
        embeddings = [await self.nvidia_service.get_embedding(chunk) for chunk in chunks]
        ids = [str(hash(chunk)) for chunk in chunks] # Simple hash for IDs, consider more robust IDs
        payloads = [{"source": file_path, "content": chunk} for chunk in chunks]

        await self.qdrant_service.upsert_vectors(ids, embeddings, payloads)
        print(f"Ingested {len(chunks)} chunks from {file_path}")