import os
import pypdf
import docx
from utils.redis_cache import cache_manager

def read_pdf(file_path: str) -> str:
    try:
        reader = pypdf.PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return ""

def read_docx(file_path: str) -> str:
    try:
        doc = docx.Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        print(f"Error reading DOCX {file_path}: {e}")
        return ""

def read_txt(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading TXT {file_path}: {e}")
        return ""

def get_session_context(uploads_dir: str, session_id: int) -> str:
    # 1. Try fetching compiled session context from Redis cache
    cached_context = cache_manager.get_session_context(session_id)
    if cached_context is not None:
        return cached_context

    session_dir = os.path.join(uploads_dir, str(session_id))
    if not os.path.exists(session_dir):
        return ""
    
    context_parts = []
    for filename in os.listdir(session_dir):
        file_path = os.path.join(session_dir, filename)
        if not os.path.isfile(file_path):
            continue
        
        # Get modification time to use as cache validator key
        try:
            mtime = os.path.getmtime(file_path)
        except Exception:
            mtime = 0.0

        # Try fetching single document text cache
        cached_doc_text = cache_manager.get_document_text(file_path, mtime)
        if cached_doc_text is not None:
            content = cached_doc_text
        else:
            ext = os.path.splitext(filename)[1].lower()
            content = ""
            if ext == ".pdf":
                content = read_pdf(file_path)
            elif ext in (".docx", ".doc"):
                content = read_docx(file_path)
            elif ext in (".txt", ".md"):
                content = read_txt(file_path)
            
            # Cache the parsed document text
            if content.strip():
                cache_manager.set_document_text(file_path, mtime, content)
        
        if content.strip():
            context_parts.append(f"--- Document: {filename} ---\n{content}\n")
            
    compiled_context = "\n".join(context_parts)
    
    # Cache compiled session context for fast repeat retrieval
    cache_manager.set_session_context(session_id, compiled_context, ttl=600)
    
    return compiled_context
