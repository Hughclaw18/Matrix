import os
import shutil
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from chat.chat_handler import ChatHandler
from utils.common import load_environment_variables
from utils.db_manager import (
    init_db,
    add_user,
    get_user,
    create_chat_session,
    get_chat_sessions,
    add_chat_message,
    get_chat_messages,
    delete_chat_session,
    clear_chat_messages,
    update_chat_session_name,
    get_user_profile,
    update_user_profile,
    get_user_id_for_session,
    get_graph_elements,
)
from utils.document_reader import get_session_context, read_pdf, read_docx, read_txt
from utils.redis_cache import cache_manager
from utils.rag_manager import rag_manager

load_environment_variables()
init_db()

app = FastAPI(title="Matrix Oracle Enterprise API", version="1.0.0")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"CRITICAL SYSTEM EXCEPTION: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Oracle System desync: {str(exc)}"}
    )

# Setup CORS for enterprise security / multi-environment access
origins = [
    "http://localhost:3000",
    "http://localhost:5173",  # Standard Vite port
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chat_handler = ChatHandler()
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads")))

# --- Pydantic Models for Scalable Request/Response Validation ---

class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    id: int
    username: str
    message: str

class SessionCreateRequest(BaseModel):
    user_id: int
    name: Optional[str] = None

class SessionRenameRequest(BaseModel):
    name: str

class ProfileUpdateRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    dob: Optional[str] = None
    email: Optional[str] = None
    profile_pic_path: Optional[str] = None

class ChatRequest(BaseModel):
    session_id: int
    message: str
    provider: Optional[str] = "gemini"
    model_name: Optional[str] = "models/gemini-3.5-flash"

# --- Authentication & Registration Endpoints ---

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    if not req.username or not req.password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    success = add_user(req.username, req.password)
    if not success:
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"message": "User registered successfully"}

@app.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    user = get_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {
        "id": user[0],
        "username": user[1],
        "message": "Login successful"
    }

# --- Profile Endpoints ---

@app.get("/profile/{user_id}")
async def get_profile(user_id: int):
    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return {
        "username": profile[0],
        "full_name": profile[1],
        "dob": profile[2],
        "email": profile[3],
        "profile_pic_path": profile[4]
    }

@app.put("/profile/{user_id}")
async def update_profile(user_id: int, req: ProfileUpdateRequest):
    update_user_profile(
        user_id,
        new_username=req.username,
        new_password=req.password,
        new_full_name=req.full_name,
        new_dob=req.dob,
        new_email=req.email,
        new_profile_pic_path=req.profile_pic_path
    )
    return {"message": "Profile updated successfully"}

# --- Session Management Endpoints ---

@app.post("/sessions")
async def create_session(req: SessionCreateRequest):
    session_id = create_chat_session(req.user_id, req.name)
    return {"session_id": session_id}

@app.get("/sessions")
async def list_sessions(user_id: int):
    sessions_db = get_chat_sessions(user_id)
    # sessions_db is a list of tuples: (id, name, timestamp)
    sessions = []
    for s in sessions_db:
        sessions.append({
            "id": s[0],
            "name": s[1],
            "timestamp": s[2]
        })
    return {"sessions": sessions}

@app.put("/sessions/{session_id}")
async def rename_session(session_id: int, req: SessionRenameRequest):
    update_chat_session_name(session_id, req.name)
    return {"message": "Session renamed successfully"}

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: int):
    user_id = get_user_id_for_session(session_id)
    delete_chat_session(session_id)
    cache_manager.invalidate_session_context(session_id)
    # Clean up uploaded files for this session
    session_upload_dir = os.path.join(UPLOAD_DIR, f"user_{user_id}", f"session_{session_id}")
    if os.path.exists(session_upload_dir):
        shutil.rmtree(session_upload_dir)
    return {"message": "Session deleted successfully"}

@app.post("/sessions/{session_id}/clear")
async def clear_session(session_id: int):
    clear_chat_messages(session_id)
    cache_manager.invalidate_session_context(session_id)
    return {"message": "Session chat history cleared"}

@app.get("/sessions/{session_id}/messages")
async def get_messages(session_id: int):
    messages_db = get_chat_messages(session_id)
    # messages_db is a list of tuples: (sender, message, timestamp)
    messages = []
    for m in messages_db:
        messages.append({
            "sender": m[0],
            "message": m[1],
            "timestamp": m[2]
        })
    return {"messages": messages}

# --- RAG Ingestion Endpoint ---

@app.post("/ingest")
async def ingest_documents(
    session_id: int = Form(...),
    files: List[UploadFile] = File(...)
):
    user_id = get_user_id_for_session(session_id)
    session_upload_dir = os.path.join(UPLOAD_DIR, f"user_{user_id}", f"session_{session_id}")
    os.makedirs(session_upload_dir, exist_ok=True)
    
    saved_files = []
    for file in files:
        safe_filename = os.path.basename(file.filename)
        if not safe_filename:
            continue
        file_path = os.path.join(session_upload_dir, safe_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(safe_filename)
        
        # Read content and feed to RAG + Knowledge Graph indexer
        ext = os.path.splitext(safe_filename)[1].lower()
        content = ""
        if ext == ".pdf":
            content = read_pdf(file_path)
        elif ext in (".docx", ".doc"):
            content = read_docx(file_path)
        elif ext in (".txt", ".md"):
            content = read_txt(file_path)
            
        if content.strip():
            rag_manager.ingest_document(session_id, safe_filename, content)
        
    cache_manager.invalidate_session_context(session_id)
        
    return {
        "message": f"Successfully ingested {len(files)} file(s)",
        "files": saved_files
    }

# --- Core Chat Endpoint with RAG Context & History Persistence ---

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Fetch session context (RAG - Hybrid + Graph Search)
    rag_context = rag_manager.retrieve_context(request.session_id, request.message)
    
    # Save the user's incoming message to SQLite database
    add_chat_message(request.session_id, "user", request.message)
    
    provider = request.provider or "gemini"
    model_name = request.model_name or "models/gemini-2.5-flash"
    
    # Check cache first
    cached_response = cache_manager.get_chat_response(provider, model_name, rag_context, request.message)
    if cached_response is not None:
        add_chat_message(request.session_id, "assistant", cached_response)
        return {"response": cached_response}
    
    try:
        # Generate the assistant response from LLMService via ChatHandler
        response = chat_handler.process_message(
            provider=provider,
            model_name=model_name,
            context=rag_context,
            question=request.message
        )
        # Cache the response
        cache_manager.set_chat_response(provider, model_name, rag_context, request.message, response, ttl=3600)
    except Exception as e:
        response = f"Neural Link Error: {str(e)}"
        
    # Save the assistant's response to SQLite database
    add_chat_message(request.session_id, "assistant", response)
    
    return {"response": response}

@app.get("/sessions/{session_id}/graph")
async def get_session_graph(session_id: int):
    entities_db, relations_db = get_graph_elements(session_id)
    user_id = get_user_id_for_session(session_id)
    
    nodes = []
    edges = []
    node_ids = set()
    
    # 1. Add entities as nodes
    for ent in entities_db:
        name = ent[0]
        etype = ent[1]
        desc = ent[2]
        if name not in node_ids:
            node_ids.add(name)
            nodes.append({
                "id": name,
                "label": name.upper(),
                "type": etype,
                "description": desc
            })
            
    # 2. Add relationships as edges
    for rel in relations_db:
        src = rel[0]
        tgt = rel[1]
        relation = rel[2]
        desc = rel[3]
        edges.append({
            "source": src,
            "target": tgt,
            "label": relation,
            "description": desc
        })
        
        for n_name in (src, tgt):
            if n_name not in node_ids:
                node_ids.add(n_name)
                nodes.append({
                    "id": n_name,
                    "label": n_name.upper(),
                    "type": "Concept",
                    "description": ""
                })
                
    # 3. Add Document Nodes & Edges
    session_upload_dir = os.path.join(UPLOAD_DIR, f"user_{user_id}", f"session_{session_id}")
    if os.path.exists(session_upload_dir):
        for filename in os.listdir(session_upload_dir):
            doc_id = f"doc:{filename}"
            if doc_id not in node_ids:
                node_ids.add(doc_id)
                nodes.append({
                    "id": doc_id,
                    "label": filename,
                    "type": "Document",
                    "description": f"Uploaded file: {filename}"
                })
                
            for ent_name in list(node_ids):
                if ent_name.startswith("doc:"):
                    continue
                edges.append({
                    "source": ent_name,
                    "target": doc_id,
                    "label": "CONTAINED_IN",
                    "description": f"Entity mentioned in {filename}"
                })
                
    return {"nodes": nodes, "edges": edges}

@app.get("/")
async def root():
    return {"message": "Welcome to the Oracle Enterprise Chatbot API"}