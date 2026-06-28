import os
import pytest
from fastapi.testclient import TestClient

# Configure mock database environment before importing app components
os.environ["TESTING"] = "True"
import utils.db_manager
utils.db_manager.DATABASE_NAME = "test_chat_history.db"

# Import app modules to test
from app.main import app
from utils.db_manager import (
    init_db,
    add_user,
    get_user,
    create_chat_session,
    get_chat_sessions,
    get_user_id_for_session,
    add_graph_entity,
    add_graph_relation,
    get_graph_elements
)
from utils.tools import calculate, matrix_lore_lookup
from utils.rag_manager import HybridGraphRAGManager

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    # Setup test database
    if os.path.exists("test_chat_history.db"):
        os.remove("test_chat_history.db")
    init_db()
    yield
    # Teardown test database
    if os.path.exists("test_chat_history.db"):
        os.remove("test_chat_history.db")

# --- 1. Test Database Operations ---

def test_db_user_registration_and_lookup():
    # Register user
    success = add_user("testneo", "matrixpass123")
    assert success is True
    
    # Retrieve user
    user = get_user("testneo", "matrixpass123")
    assert user is not None
    assert user[1] == "testneo"
    
    # Check incorrect credentials
    bad_user = get_user("testneo", "wrongpass")
    assert bad_user is None

def test_db_session_mapping():
    # Query test user id
    user = get_user("testneo", "matrixpass123")
    user_id = user[0]
    
    # Create session
    session_id = create_chat_session(user_id, "Nebuchadnezzar Deck")
    assert session_id > 0
    
    # Verify user_id mapping from session_id
    mapped_user_id = get_user_id_for_session(session_id)
    assert mapped_user_id == user_id
    
    # List sessions
    sessions = get_chat_sessions(user_id)
    assert len(sessions) > 0
    assert sessions[0][1] == "Nebuchadnezzar Deck"

def test_db_graph_elements():
    session_id = 9999  # Mock session
    
    # Add entities
    success1 = add_graph_entity(session_id, "neo", "Person", "The One")
    success2 = add_graph_entity(session_id, "trinity", "Person", "Officer")
    assert success1 is True
    assert success2 is True
    
    # Add relationships
    success3 = add_graph_relation(session_id, "neo", "trinity", "LOVES", "Proximity match")
    assert success3 is True
    
    # Query elements
    entities, relations = get_graph_elements(session_id)
    assert len(entities) == 2
    assert len(relations) == 1
    assert entities[0][0] == "neo"
    assert relations[0][0] == "neo"
    assert relations[0][1] == "trinity"
    assert relations[0][2] == "LOVES"

# --- 2. Test ReAct Tools ---

def test_tool_calculate():
    res1 = calculate("2 * (3 + 4)")
    assert "Result: 14" in res1
    
    res2 = calculate("100 / 5")
    assert "Result: 20.0" in res2
    
    # Test protection against arbitrary syntax code execution
    res3 = calculate("import os; os.system('ls')")
    assert "Result" not in res3 # Blocked or evaluation error

def test_tool_matrix_lore_lookup():
    res1 = matrix_lore_lookup("zion")
    assert "zion" in res1.lower()
    assert "last human city" in res1.lower()
    
    res2 = matrix_lore_lookup("architect")
    assert "creator of the matrix" in res2.lower()
    
    res3 = matrix_lore_lookup("unknown_lore_term")
    assert "not found" in res3.lower()

# --- 3. Test Graph RAG Helper Methods ---

def test_rag_chunking():
    # Instantiate manager
    rag = HybridGraphRAGManager()
    
    # Verify character length chunking behavior
    text = "A" * 1000
    chunks = rag._chunk_text(text, chunk_size=300, overlap=50)
    assert len(chunks) > 1
    assert all(len(c) <= 300 for c in chunks)

# --- 4. Test FastAPI Endpoint client requests ---

def test_api_root():
    res = client.get("/")
    assert res.status_code == 200
    assert "Oracle Enterprise Chatbot API" in res.json()["message"]

def test_api_session_graph():
    # Test fetching session graph (should return empty node/edge list or populate docs)
    res = client.get("/sessions/9999/graph")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "edges" in data
    
    # Verify mock entities added in test_db_graph_elements are loaded
    node_ids = [n["id"] for n in data["nodes"]]
    assert "neo" in node_ids
    assert "trinity" in node_ids

if __name__ == '__main__':
    print("Running backend tests directly...")
    import sys
    # Initialize DB Mock Setup
    if os.path.exists("test_chat_history.db"):
        os.remove("test_chat_history.db")
    init_db()
    
    try:
        test_db_user_registration_and_lookup()
        print("1. User registration & lookup: PASSED")
        test_db_session_mapping()
        print("2. Session database mapping: PASSED")
        test_db_graph_elements()
        print("3. Relational Knowledge Graph insertion: PASSED")
        test_tool_calculate()
        print("4. Math calculator tool sandbox: PASSED")
        test_tool_matrix_lore_lookup()
        print("5. Matrix core lore lookup tool: PASSED")
        test_rag_chunking()
        print("6. RAG character chunking overlaps: PASSED")
        test_api_root()
        print("7. FastAPI root API welcome endpoint: PASSED")
        test_api_session_graph()
        print("8. Graph visualizer REST JSON schemas: PASSED")
        print("\n=== ALL TESTS PASSED SUCCESSFULLY! ===")
    except Exception as e:
        print(f"\n!!! TEST FAILED: {e} !!!")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if os.path.exists("test_chat_history.db"):
            os.remove("test_chat_history.db")
