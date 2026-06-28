# 🟢 Architectural Flows - Matrix Oracle Workspace

This document provides step-by-step technical walkthroughs for the core architectural flows of the **Matrix Oracle Chatbot and Operator Workspace**.

---

## Flow 1: Operator Authentication & Session Setup

### Description:
Validates operator credentials, loads matching user settings, and initializes active connection pathways (sessions).

### Detailed Steps:
1. **Login request**: The React client encrypts the login form and posts to `POST /login` with username and password.
2. **Password Verification**:
   * The backend queries the `users` table for the matching username.
   * If found, it executes `bcrypt.checkpw()` to compare the user's password string against the hashed database entry.
3. **Session Fetch**:
   * On successful verification, the client stores authentication metadata in browser `localStorage`.
   * The client makes a `GET /sessions?user_id=X` call.
4. **SQLite/Postgres Retrieval**:
   * The database helper fetches active sessions ordered by the latest timestamps.
   * The active sessions are returned as a JSON array to populate the left sidebar navigation.
5. **Path Activation**:
   * Selecting a session sets the active `currentSessionId` in React, fetching messages via `GET /sessions/{session_id}/messages`.

---

## Flow 2: Scalable Document Ingestion (Hybrid Graph RAG)

### Description:
Processes uploaded PDFs, indexes semantic vectors locally in Qdrant, and builds a relational knowledge graph in SQLite/PostgreSQL.

### Detailed Steps:
1. **Document Upload**: The operator drops files into the file dropzone. The React client makes a multipart form request to `POST /ingest` passing the `session_id`.
2. **Path Sanitization**: The FastAPI backend extracts filenames using `os.path.basename` to prevent directory traversal attacks.
3. **Text Extraction**:
   * PDF files are parsed using `pypdf.PdfReader`.
   * DOCX files are parsed using `docx.Document`.
   * Text/Markdown files are read using standard utf-8 file readers.
4. **Text Chunking**:
   * The parsed text is chunked into 600-character segments with 120-character overlaps.
5. **Vector Indexing (Qdrant)**:
   * The backend calls Gemini `text-embedding-004` to compute 768-dimensional dense vectors in batches of 32.
   * Chunks and dense vectors are upserted into the local Qdrant collection with `session_id` metadata payload tags.
6. **Knowledge Graph Extraction (Graph RAG)**:
   * The backend scans each text chunk against a dictionary of known Matrix terms (Neo, Zion, Morpheus, Agent Smith) and Computer Science concepts (DFS, BFS, cryptography, database).
   * Matched entities are logged into the `graph_entities` table in SQLite/PostgreSQL.
   * Proximity matches (co-occurring entities in the same chunk) are parsed for verbs (e.g. loves, commands, created) and written to the `graph_relations` table.
7. **Cache Invalidation**:
   * The compiled context cache for this session is purged from Redis (`session_context:{session_id}` key deleted) to force retrieval updates.

---

## Flow 3: Unified Chat Retrieval & ReAct Execution

### Description:
Fuses Hybrid semantic-lexical vector lookups with Graph entity relationships, checks the Redis cache, and manages the ReAct tool calling execution loops.

### Detailed Steps:
1. **Query Submission**: The operator enters a query in the chatbox. The client POSTs to `POST /chat` with the `session_id`, message, LLM provider, and model name.
2. **Context Retrieval**:
   * **Dense Retrieval**: Qdrant searches the vector database using the query's Gemini embedding, filtering by the active `session_id`.
   * **Sparse Retrieval**: A fast TF-IDF lexical index runs over the session's chunks to capture exact keyword matches.
   * **Graph Retrieval**: The query is parsed to identify known entities. Matching entity details and relationships are queried from SQLite/PostgreSQL (`graph_entities` and `graph_relations` tables).
   * **Fusion**: Semantic text chunks, lexical keyword matches, and entity relationship triples are combined into a structured prompt context block.
3. **Completion Cache Lookup**:
   * The backend hashes the prompt, model, and context. It queries Redis for this hash.
   * If a cache hit occurs, the cached text response is retrieved and returned to the client in milliseconds.
4. **ReAct Agent Loop Execution**:
   * If a cache miss occurs, the LLMService is invoked. The system prompt instructs the model to request tools when needed by writing `TOOL: tool_name(argument)`.
   * **Step 1 (Reasoning)**: The LLM processes the query. If it outputs a tool call (e.g. `TOOL: calculate(256 * 1024)` or `TOOL: web_search(who directed Matrix Resurrections)`):
     * The backend intercepts the output and runs the requested function from `utils/tools.py`.
     * The tool output is appended to the prompt history as `SYSTEM DATA RETRIEVED`.
   * **Step 2 (Acting)**: The LLM is prompted again with the updated history containing the tool results.
   * **Step 3 (Final Answer)**: The LLM formulates its final response in the Oracle's characteristic tone.
5. **Logging & Return**:
   * The assistant response is stored in Redis (with a 1-hour TTL) and written to the `chat_messages` table in SQLite/PostgreSQL.
   * The text is returned to the client, triggering the retro character-reveal decoding animation on the screen.
