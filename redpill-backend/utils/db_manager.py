import os
import sqlite3
import bcrypt
from typing import List, Tuple, Optional

# Check for Postgres configurations
POSTGRES_URL = os.getenv("DATABASE_URL")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")

USE_POSTGRES = False
if POSTGRES_URL or (POSTGRES_HOST and POSTGRES_USER and POSTGRES_DB):
    try:
        import psycopg2
        USE_POSTGRES = True
        print(f"Database engine: PostgreSQL (Host: {POSTGRES_HOST or 'URL'})")
    except ImportError:
        print("psycopg2-binary not installed, falling back to SQLite.")

DATABASE_NAME = "chat_history.db"

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def get_db_connection():
    if USE_POSTGRES:
        if POSTGRES_URL:
            return psycopg2.connect(POSTGRES_URL)
        else:
            return psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                dbname=POSTGRES_DB
            )
    else:
        return sqlite3.connect(DATABASE_NAME, timeout=15.0)

def q(query_string: str) -> str:
    """Helper to convert standard SQLite '?' placeholders to PostgreSQL '%s' dynamically."""
    if USE_POSTGRES:
        return query_string.replace("?", "%s")
    return query_string

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        if USE_POSTGRES:
            c.execute("""CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT,
                dob TEXT,
                email TEXT,
                profile_pic_path TEXT
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS chat_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                session_id INTEGER NOT NULL,
                sender VARCHAR(50) NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS graph_entities (
                id SERIAL PRIMARY KEY,
                session_id INTEGER NOT NULL,
                name VARCHAR(255) NOT NULL,
                type VARCHAR(100),
                description TEXT,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
                UNIQUE(session_id, name)
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS graph_relations (
                id SERIAL PRIMARY KEY,
                session_id INTEGER NOT NULL,
                source VARCHAR(255) NOT NULL,
                target VARCHAR(255) NOT NULL,
                relation VARCHAR(100) NOT NULL,
                description TEXT,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
                UNIQUE(session_id, source, target, relation)
            )""")
        else:
            c.execute("""CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT,
                dob TEXT,
                email TEXT,
                profile_pic_path TEXT
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS graph_entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                type TEXT,
                description TEXT,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id),
                UNIQUE(session_id, name)
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS graph_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                relation TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id),
                UNIQUE(session_id, source, target, relation)
            )""")
        conn.commit()
    except Exception as e:
        print(f"Database Initialization Error: {e}")
    finally:
        conn.close()

def add_user(username, password) -> bool:
    conn = get_db_connection()
    c = conn.cursor()
    try:
        hashed = hash_password(password)
        c.execute(q("INSERT INTO users (username, password) VALUES (?, ?)"), (username, hashed))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding user: {e}")
        return False
    finally:
        conn.close()

def get_user(username, password) -> Optional[Tuple]:
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(q("SELECT id, username, password FROM users WHERE username = ?"), (username,))
        user = c.fetchone()
        if user and (user[2] == password or verify_password(password, user[2])):
            return user
        return None
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None
    finally:
        conn.close()

def create_chat_session(user_id: int, name: str) -> int:
    conn = get_db_connection()
    c = conn.cursor()
    try:
        if USE_POSTGRES:
            c.execute("INSERT INTO chat_sessions (user_id, name) VALUES (%s, %s) RETURNING id", (user_id, name))
            session_id = c.fetchone()[0]
        else:
            c.execute("INSERT INTO chat_sessions (user_id, name) VALUES (?, ?)", (user_id, name))
            session_id = c.lastrowid
        conn.commit()
        return session_id
    except Exception as e:
        print(f"Error creating chat session: {e}")
        return 0
    finally:
        conn.close()

def get_chat_sessions(user_id: int) -> List[Tuple]:
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(q("SELECT id, name, timestamp FROM chat_sessions WHERE user_id = ? ORDER BY timestamp DESC"), (user_id,))
        return c.fetchall()
    except Exception as e:
        print(f"Error fetching sessions: {e}")
        return []
    finally:
        conn.close()

def add_chat_message(session_id: int, sender: str, message: str) -> bool:
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(q("INSERT INTO chat_messages (session_id, sender, message) VALUES (?, ?, ?)"), (session_id, sender, message))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding chat message: {e}")
        return False
    finally:
        conn.close()

def get_chat_messages(session_id: int) -> List[Tuple]:
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(q("SELECT sender, message, timestamp FROM chat_messages WHERE session_id = ? ORDER BY id ASC"), (session_id,))
        return c.fetchall()
    except Exception as e:
        print(f"Error fetching chat messages: {e}")
        return []
    finally:
        conn.close()

def delete_chat_session(session_id: int) -> bool:
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(q("DELETE FROM chat_sessions WHERE id = ?"), (session_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting chat session: {e}")
        return False
    finally:
        conn.close()

def clear_chat_messages(session_id: int) -> bool:
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(q("DELETE FROM chat_messages WHERE session_id = ?"), (session_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error clearing chat messages: {e}")
        return False
    finally:
        conn.close()

def update_chat_session_name(session_id: int, new_name: str) -> bool:
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(q("UPDATE chat_sessions SET name = ? WHERE id = ?"), (new_name, session_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating session name: {e}")
        return False
    finally:
        conn.close()

def get_user_profile(user_id: int) -> Optional[Tuple]:
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(q("SELECT id, username, full_name, dob, email, profile_pic_path FROM users WHERE id = ?"), (user_id,))
        return c.fetchone()
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        return None
    finally:
        conn.close()

def update_user_profile(user_id: int, new_username=None, new_password=None, new_full_name=None, new_dob=None, new_email=None, new_profile_pic_path=None) -> bool:
    conn = get_db_connection()
    c = conn.cursor()
    try:
        updates = []
        params = []
        if new_username:
            updates.append("username = ?")
            params.append(new_username)
        if new_password:
            updates.append("password = ?")
            params.append(hash_password(new_password))
        if new_full_name is not None:
            updates.append("full_name = ?")
            params.append(new_full_name)
        if new_dob is not None:
            updates.append("dob = ?")
            params.append(new_dob)
        if new_email is not None:
            updates.append("email = ?")
            params.append(new_email)
        if new_profile_pic_path is not None:
            updates.append("profile_pic_path = ?")
            params.append(new_profile_pic_path)

        if updates:
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            params.append(user_id)
            c.execute(q(query), tuple(params))
            conn.commit()
        return True
    except Exception as e:
        print(f"Error updating user profile: {e}")
        return False
    finally:
        conn.close()

def add_graph_entity(session_id: int, name: str, entity_type: str, description: str) -> bool:
    conn = get_db_connection()
    c = conn.cursor()
    try:
        if USE_POSTGRES:
            c.execute("""INSERT INTO graph_entities (session_id, name, type, description)
                         VALUES (%s, %s, %s, %s)
                         ON CONFLICT (session_id, name)
                         DO UPDATE SET type = EXCLUDED.type, description = EXCLUDED.description""",
                      (session_id, name, entity_type, description))
        else:
            c.execute("""INSERT OR REPLACE INTO graph_entities (session_id, name, type, description)
                         VALUES (?, ?, ?, ?)""", (session_id, name, entity_type, description))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding graph entity: {e}")
        return False
    finally:
        conn.close()

def add_graph_relation(session_id: int, source: str, target: str, relation: str, description: str) -> bool:
    conn = get_db_connection()
    c = conn.cursor()
    try:
        if USE_POSTGRES:
            c.execute("""INSERT INTO graph_relations (session_id, source, target, relation, description)
                         VALUES (%s, %s, %s, %s, %s)
                         ON CONFLICT (session_id, source, target, relation)
                         DO UPDATE SET description = EXCLUDED.description""",
                      (session_id, source, target, relation, description))
        else:
            c.execute("""INSERT OR REPLACE INTO graph_relations (session_id, source, target, relation, description)
                         VALUES (?, ?, ?, ?, ?)""", (session_id, source, target, relation, description))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding graph relation: {e}")
        return False
    finally:
        conn.close()

def get_graph_elements(session_id: int) -> Tuple[List[Tuple], List[Tuple]]:
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(q("SELECT name, type, description FROM graph_entities WHERE session_id = ?"), (session_id,))
        entities = c.fetchall()
        c.execute(q("SELECT source, target, relation, description FROM graph_relations WHERE session_id = ?"), (session_id,))
        relations = c.fetchall()
        return entities, relations
    except Exception as e:
        print(f"Error fetching graph elements: {e}")
        return [], []
    finally:
        conn.close()

def get_user_id_for_session(session_id: int) -> int:
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(q("SELECT user_id FROM chat_sessions WHERE id = ?"), (session_id,))
        res = c.fetchone()
        return res[0] if res else 0
    except Exception as e:
        print(f"Error fetching user_id for session: {e}")
        return 0
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized.")