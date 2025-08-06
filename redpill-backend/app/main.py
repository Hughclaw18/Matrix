from fastapi import FastAPI
from pydantic import BaseModel
from chat.chat_handler import ChatHandler
from utils.common import load_environment_variables

load_environment_variables()

app = FastAPI()
chat_handler = ChatHandler()

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    response = chat_handler.process_message(request.message)
    return {"response": response}

@app.get("/")
async def root():
    return {"message": "Welcome to the NVIDIA NIM Chatbot API"}