from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from chat.chat_handler import ChatHandler
from utils.common import load_environment_variables

load_environment_variables()

app = FastAPI()
chat_handler = ChatHandler()

origins = [
    "http://localhost:3000",
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    response = chat_handler.process_message(context="", question=request.message)
    return {"response": response}

@app.get("/")
async def root():
    return {"message": "Welcome to the NVIDIA NIM Chatbot API"}