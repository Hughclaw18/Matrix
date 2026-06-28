import os
import re
import math
from google import genai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from utils.db_manager import add_graph_entity, add_graph_relation, get_graph_elements, get_user_id_for_session

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
QDRANT_PATH = os.path.join(PROJECT_ROOT, "qdrant_db")
COLLECTION_NAME = "matrix_rag"

# List of known entities for the pattern-based Graph RAG extractor
MATRIX_ENTITIES = {
    "neo": ("Person", "The One, key savior of Zion, capable of manipulating the Matrix core."),
    "morpheus": ("Person", "Captain of the Nebuchadnezzar, mentor to Neo."),
    "trinity": ("Person", "First officer of the Nebuchadnezzar, Neo's love interest."),
    "agent smith": ("Program", "Former Agent of the Matrix, rogue self-replicating virus."),
    "architect": ("Program", "The creator of the Matrix, representing strict mathematical logic."),
    "oracle": ("Program", "Intelligent system designed to understand human psychology and choices."),
    "zion": ("Place", "The last underground city of humanity near the Earth's core."),
    "nebuchadnezzar": ("Ship", "Morpheus' hovercraft, destroyed by sentinels via EMP."),
    "sentinel": ("Machine", "Multi-tentacled squid-like search-and-destroy machines built by the Machine City."),
    "keymaker": ("Program", "Exiled program capable of creating shortcut keys to access the Source."),
    "merovingian": ("Program", "Power broker program operating an exile smuggling ring in the Matrix."),
    "agent jones": ("Program", "Standard Matrix Agent capable of dodging bullets."),
    "agent brown": ("Program", "Standard Matrix Agent tasked with capturing Morpheus."),
    "persephone": ("Program", "Merovingian's wife, helps Neo's crew in exchange for a kiss."),
    "cypher": ("Person", "Nebuchadnezzar crew member who betrays Morpheus to return to the Matrix simulation.")
}

CS_ENTITIES = {
    "binary tree": ("Data Structure", "A hierarchical tree structure where each node has at most two children."),
    "bfs": ("Algorithm", "Breadth-First Search, traverses tree/graph level by level."),
    "dfs": ("Algorithm", "Depth-First Search, traverses deep down branches before backtracking."),
    "sorting": ("Algorithm", "Ordering list elements (e.g. QuickSort, MergeSort)."),
    "cryptography": ("Concept", "Securing information via encryption, decryption, and hash loops."),
    "compiler": ("Program", "Translates source code in high-level programming language into machine code."),
    "database": ("System", "Organized collection of data (e.g. relational SQL, vector collections)."),
    "cybersecurity": ("Concept", "Defending networks and systems from digital attackers.")
}

ALL_KNOWN_ENTITIES = {**MATRIX_ENTITIES, **CS_ENTITIES}

class HybridGraphRAGManager:
    def __init__(self):
        self._qdrant_client_inst = None

    @property
    def qdrant_client(self):
        if self._qdrant_client_inst is not None:
            return self._qdrant_client_inst
            
        import sys
        if "pytest" in sys.modules or os.getenv("TESTING") == "True":
            client = QdrantClient(":memory:")
        else:
            os.makedirs(QDRANT_PATH, exist_ok=True)
            client = QdrantClient(path=QDRANT_PATH)
        
        try:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
        except Exception:
            pass
            
        self._qdrant_client_inst = client
        return client

    def _get_dense_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Fetch dense semantic embeddings from Gemini API. Fallback to zero vectors on failure."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return [[0.0] * 768 for _ in texts]
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.embed_content(
                model="text-embedding-004",
                contents=texts
            )
            if hasattr(response, "embeddings"):
                return [emb.values for emb in response.embeddings]
            elif isinstance(response, dict) and "embedding" in response:
                return response["embedding"]
            return [[0.0] * 768 for _ in texts]
        except Exception as e:
            print(f"Gemini Embeddings API Error: {e}. Returning zero vectors.")
            return [[0.0] * 768 for _ in texts]

    def _get_query_embedding(self, query: str) -> list[float]:
        """Fetch dense query embedding."""
        res = self._get_dense_embeddings([query])
        return res[0]

    def _chunk_text(self, text: str, chunk_size: int = 600, overlap: int = 120) -> list[str]:
        """Chunk text with character overlap."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return [c.strip() for c in chunks if len(c.strip()) > 30]

    def ingest_document(self, session_id: int, filename: str, content: str) -> None:
        """Processes a document, chunking, indexing vectors, and building a knowledge graph in SQLite."""
        if not content.strip():
            return
            
        chunks = self._chunk_text(content)
        if not chunks:
            return

        # 1. Index Dense Vectors into Qdrant in batches
        embeddings = self._get_dense_embeddings(chunks)
        
        points = []
        for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            point_id = hash(f"{session_id}:{filename}:{idx}") & 0xFFFFFFFFFFFFFFFF
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "session_id": session_id,
                        "filename": filename,
                        "text": chunk,
                        "chunk_index": idx
                    }
                )
            )
            
        self.qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        print(f"Indexed {len(chunks)} chunks into Qdrant collection for session {session_id}.")

        # 2. Extract Entities & Relations for Graph RAG (Stored in SQLite)
        for chunk in chunks:
            # Find entities mentioned in the chunk
            found_entities = []
            chunk_lower = chunk.lower()
            for entity_name, (etype, desc) in ALL_KNOWN_ENTITIES.items():
                if entity_name in chunk_lower:
                    found_entities.append(entity_name)
                    # Add entity to session SQLite graph
                    add_graph_entity(session_id, entity_name, etype, desc)

            # Establish proximity relationships: if entities occur in same chunk, they are related!
            # Also extract some basic lexical relationships (e.g. Neo loves Trinity)
            for i in range(len(found_entities)):
                for j in range(i + 1, len(found_entities)):
                    e1 = found_entities[i]
                    e2 = found_entities[j]
                    
                    relation = "MENTIONED_WITH"
                    desc = f"Both entities appear in context of {filename}"
                    
                    # Pattern matching overlays
                    chunk_seg = chunk_lower[chunk_lower.find(e1):chunk_lower.find(e2)+len(e2)]
                    if "love" in chunk_seg or "kiss" in chunk_seg:
                        relation = "LOVES"
                    elif "seek" in chunk_seg or "find" in chunk_seg or "prophecy" in chunk_seg:
                        relation = "SEEKING"
                    elif "destroy" in chunk_seg or "fight" in chunk_seg or "enemy" in chunk_seg:
                        relation = "HOSTILE_TO"
                    elif "command" in chunk_seg or "captain" in chunk_seg or "ship" in chunk_seg:
                        relation = "COMMANDS"
                    elif "create" in chunk_seg or "make" in chunk_seg or "author" in chunk_seg:
                        relation = "CREATED"

                    add_graph_relation(session_id, e1, e2, relation, desc)

    def retrieve_context(self, session_id: int, query: str, top_k: int = 3) -> str:
        """Hybrid Graph RAG retrieval combining dense, sparse (BM25 lexical), and relational entity sub-graphs."""
        
        # --- 1. DENSE VECTOR SEARCH (QDRANT) ---
        query_vector = self._get_query_embedding(query)
        dense_results = self.qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter={
                "must": [
                    {"key": "session_id", "match": {"value": session_id}}
                ]
            },
            limit=top_k * 2
        )
        
        dense_chunks = [hit.payload["text"] for hit in dense_results]

        # --- 2. SPARSE LEXICAL SEARCH (BM25/TF-IDF) ---
        # Implement a fast TF-IDF term scoring against all chunks in Qdrant for this session
        all_session_points = self.qdrant_client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter={
                "must": [
                    {"key": "session_id", "match": {"value": session_id}}
                ]
            },
            limit=1000 # Scroll up to 1000 chunks for this session
        )[0]
        
        sparse_chunks = []
        if all_session_points:
            query_words = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]
            scored_chunks = []
            
            # Simple TF-IDF score
            for pt in all_session_points:
                text = pt.payload["text"]
                text_lower = text.lower()
                score = 0
                for word in query_words:
                    count = text_lower.count(word)
                    if count > 0:
                        # TF weight * simple IDF weight (1.0 default)
                        score += (count / len(text_lower.split())) * 1.0
                if score > 0:
                    scored_chunks.append((score, text))
            
            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            sparse_chunks = [txt for _, txt in scored_chunks[:2]]

        # --- 3. GRAPH RAG SEARCH (SQLite Subgraph Extraction) ---
        # Extract entities mentioned in query
        query_lower = query.lower()
        entities_db, relations_db = get_graph_elements(session_id)
        
        relevant_entities = []
        for ent in entities_db:
            # ent is (name, type, description)
            ename = ent[0].lower()
            if ename in query_lower:
                relevant_entities.append(ent)
                
        # Find relationships connecting these queried entities
        matching_relations = []
        for rel in relations_db:
            # rel is (source, target, relation, description)
            src = rel[0].lower()
            tgt = rel[1].lower()
            # If relationship connects any queried entities
            if any(e[0].lower() in (src, tgt) for e in relevant_entities):
                matching_relations.append(f"- {rel[0]} --({rel[2]})--> {rel[1]} : {rel[3]}")

        # --- 4. CONTEXT FUSION ---
        # Merge semantic dense context, keyword sparse context, and knowledge graph relationships
        merged_chunks = []
        
        # Deduplicate dense and sparse chunks
        seen = set()
        for chunk in dense_chunks + sparse_chunks:
            chunk_hash = hash(chunk)
            if chunk_hash not in seen:
                seen.add(chunk_hash)
                merged_chunks.append(chunk)

        # Truncate to top_k * 2 to keep context size healthy
        final_chunks = merged_chunks[:top_k + 1]
        
        context_parts = []
        if final_chunks:
            context_parts.append("=== Semantic Text Chunks (Dense + Sparse Search) ===")
            for idx, chk in enumerate(final_chunks):
                context_parts.append(f"[{idx+1}] {chk}\n")
                
        if relevant_entities:
            context_parts.append("=== Entity Knowledge Graph (Graph RAG) ===")
            for ent in relevant_entities:
                context_parts.append(f"Entity: {ent[0]} (Type: {ent[1]}) - {ent[2]}")
            if matching_relations:
                context_parts.append("\nRelationships:")
                context_parts.extend(matching_relations[:6]) # Cap relations to avoid clutter
                
        return "\n".join(context_parts)

# Singleton manager
rag_manager = HybridGraphRAGManager()
