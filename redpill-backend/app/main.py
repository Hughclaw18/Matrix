from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File
from chat.chat_handler import ChatHandler
from ingestion.data_loader import DataLoader
from ingestion.document_parser import DocumentParser
from utils.common import load_environment_variables

# Load environment variables at startup
load_environment_variables()

app = FastAPI()
chat_handler = ChatHandler()
data_loader = DataLoader()
document_parser = DocumentParser()

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    response = chat_handler.process_message(request.message)
    return {"response": response}

@app.get("/")
async def root():
    return {"message": "Welcome to the Multimodal RAG Chatbot API"}

@app.post("/ingest")
async def ingest_document_endpoint(file: UploadFile = File(...)):
    try:
        # Save the uploaded file temporarily
        file_path = f"./temp_{file.filename}"
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        # Ingest the document using DataLoader
        await data_loader.ingest_document(file_path)

        # Clean up the temporary file
        import os
        os.remove(file_path)

        return {"message": f"Document {file.filename} ingested successfully"}
    except Exception as e:
        return {"message": f"Error ingesting document: {e}"}