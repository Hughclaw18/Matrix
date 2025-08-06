import sqlite3
import os

DATABASE_NAME = "chat_history.db"

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
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
    conn.commit()
    conn.close()

def add_user(username, password):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user(username, password):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

def create_chat_session(user_id, name=None):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO chat_sessions (user_id, name) VALUES (?, ?)", (user_id, name))
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_chat_sessions(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name, timestamp FROM chat_sessions WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    sessions = c.fetchall()
    conn.close()
    return sessions

def add_chat_message(session_id, sender, message):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO chat_messages (session_id, sender, message) VALUES (?, ?, ?)", (session_id, sender, message))
    conn.commit()
    conn.close()

def get_chat_messages(session_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT sender, message, timestamp FROM chat_messages WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
    messages = c.fetchall()
    conn.close()
    return messages

def delete_chat_session(session_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    c.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

def clear_chat_messages(session_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

def update_chat_session_name(session_id, new_name):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("UPDATE chat_sessions SET name = ? WHERE id = ?", (new_name, session_id))
    conn.commit()
    conn.close()

def get_user_profile(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT username, full_name, dob, email, profile_pic_path FROM users WHERE id = ?", (user_id,))
    profile = c.fetchone()
    conn.close()
    return profile

def update_user_profile(user_id, new_username=None, new_password=None, new_full_name=None, new_dob=None, new_email=None, new_profile_pic_path=None):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    updates = []
    params = []
    if new_username:
        updates.append("username = ?")
        params.append(new_username)
    if new_password:
        updates.append("password = ?")
        params.append(new_password)
    if new_full_name:
        updates.append("full_name = ?")
        params.append(new_full_name)
    if new_dob:
        updates.append("dob = ?")
        params.append(new_dob)
    if new_email:
        updates.append("email = ?")
        params.append(new_email)
    if new_profile_pic_path:
        updates.append("profile_pic_path = ?")
        params.append(new_profile_pic_path)

    if updates:
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        params.append(user_id)
        c.execute(query, tuple(params))
        conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized.")