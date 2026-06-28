import os
import hashlib
import json
import redis
from typing import Optional

class RedisCacheManager:
    def __init__(self):
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", 6379))
        password = os.getenv("REDIS_PASSWORD", None)
        if password == "":
            password = None
        
        self.enabled = False
        self.redis_client = None
        self.fallback_cache = {}  # In-memory fallback dictionary
        
        try:
            # Short connection timeout so we don't hang if Redis is down
            # Force RESP2 (protocol=2) to prevent auth/protocol collisions (HELLO errors) on protected Redis servers
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                password=password,
                decode_responses=True,
                socket_connect_timeout=2.0,
                protocol=2
            )
            # Ping to verify active connection
            self.redis_client.ping()
            self.enabled = True
            print("Redis connection established. Caching enabled.")
        except Exception as e:
            print(f"Redis not available ({e}). Falling back to local in-memory cache.")

    def _hash_key(self, *args) -> str:
        string_to_hash = ":".join(str(arg) for arg in args)
        return hashlib.md5(string_to_hash.encode('utf-8')).hexdigest()

    def get(self, key: str) -> Optional[str]:
        if self.enabled:
            try:
                return self.redis_client.get(key)
            except Exception as e:
                print(f"Redis get error: {e}")
        return self.fallback_cache.get(key)

    def set(self, key: str, value: str, ttl: int = 3600) -> None:
        if self.enabled:
            try:
                self.redis_client.set(key, value, ex=ttl)
                return
            except Exception as e:
                print(f"Redis set error: {e}")
        self.fallback_cache[key] = value

    def delete(self, key: str) -> None:
        if self.enabled:
            try:
                self.redis_client.delete(key)
                return
            except Exception as e:
                print(f"Redis delete error: {e}")
        if key in self.fallback_cache:
            del self.fallback_cache[key]

    # --- Context & Chat caching methods ---

    def get_chat_response(self, provider: str, model_name: str, context: str, question: str) -> Optional[str]:
        # Hash context to keep keys short and efficient
        context_hash = hashlib.md5(context.encode('utf-8')).hexdigest() if context else "no_context"
        key = f"chat:{provider}:{model_name}:{context_hash}:{self._hash_key(question)}"
        return self.get(key)

    def set_chat_response(self, provider: str, model_name: str, context: str, question: str, response: str, ttl: int = 3600) -> None:
        context_hash = hashlib.md5(context.encode('utf-8')).hexdigest() if context else "no_context"
        key = f"chat:{provider}:{model_name}:{context_hash}:{self._hash_key(question)}"
        self.set(key, response, ttl=ttl)

    def get_document_text(self, file_path: str, mtime: float) -> Optional[str]:
        # Cache single parsed document text. Invalidate if modification time changes.
        key = f"doc:{self._hash_key(file_path)}:{mtime}"
        return self.get(key)

    def set_document_text(self, file_path: str, mtime: float, text: str, ttl: int = 86400) -> None:
        key = f"doc:{self._hash_key(file_path)}:{mtime}"
        self.set(key, text, ttl=ttl)

    def get_session_context(self, session_id: int) -> Optional[str]:
        # Cache compiled RAG context for a given session
        key = f"session_context:{session_id}"
        return self.get(key)

    def set_session_context(self, session_id: int, context: str, ttl: int = 600) -> None:
        key = f"session_context:{session_id}"
        self.set(key, context, ttl=ttl)

    def invalidate_session_context(self, session_id: int) -> None:
        key = f"session_context:{session_id}"
        self.delete(key)

# Global singleton
cache_manager = RedisCacheManager()
