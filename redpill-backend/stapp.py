import streamlit as st
import sys
import os
import streamlit as st

# --- Setup and Imports ---
# Add project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.common import load_environment_variables
load_environment_variables()
from services.google_chat_service import GoogleChatService
from utils.db_manager import init_db, add_user, get_user, create_chat_session, get_chat_sessions, add_chat_message, get_chat_messages, delete_chat_session, clear_chat_messages, update_chat_session_name, update_user_profile, get_user_profile, DATABASE_NAME

# --- Page Configuration ---
st.set_page_config(page_title="Matrix Oracle Interface", page_icon="🤖", layout="wide")

# --- Database Initialization ---
init_db()

# --- Helper Functions ---
@st.cache_resource
def get_google_chat_service():
    """Initialize and cache the GoogleChatService."""
    return GoogleChatService()

def logout():
    """Clear session state variables to log the user out."""
    keys_to_delete = ["logged_in", "user_id", "username", "current_session_id", "messages"]
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# --- UI Rendering Functions ---

def render_login_page():
    """Render the login and signup UI."""
    st.title("Welcome to 🤖 Matrix Oracle Interface")
    st.markdown("Your guide to the Matrix.")

    # Center the login/signup form
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

            with login_tab:
                with st.form("login_form"):
                    st.subheader("Login to your account")
                    login_username = st.text_input("Username", key="login_username")
                    login_password = st.text_input("Password", type="password", key="login_password")
                    submitted = st.form_submit_button("Login")
                    if submitted:
                        user = get_user(login_username, login_password)
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user[0]
                            st.session_state.username = user[1]
                            st.rerun()
                        else:
                            st.error("Invalid username or password")

            with signup_tab:
                with st.form("signup_form"):
                    st.subheader("Create a new account")
                    signup_username = st.text_input("New Username", key="signup_username")
                    signup_password = st.text_input("New Password", type="password", key="signup_password")
                    submitted = st.form_submit_button("Sign Up")
                    if submitted:
                        if add_user(signup_username, signup_password):
                            st.success("Account created successfully! Please login.")
                        else:
                            st.error("Username already exists. Please choose another.")

def render_main_app():
    """Render the main chat application UI after login."""
    google_chat_service = get_google_chat_service()
    
    # --- Sidebar for Session Management ---
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.username}!")
        if st.button("Logout"):
            logout()
        
        if st.button("User Profile"):
            st.session_state.current_view = "profile"
            st.rerun()

        st.divider()
        st.header("Chat Sessions")

        if st.button("➕ New Chat"):
            st.session_state.current_session_id = create_chat_session(st.session_state.user_id, None)
            st.session_state.messages = []
            st.rerun()

        sessions = get_chat_sessions(st.session_state.user_id)
        if sessions:
            # Create a mapping from a display name to session ID
            session_options = {s[0]: f"Session {s[0]} - {s[2].split(' ')[0]}" for s in sessions}
            
            # Function to be called when a session is selected
            def on_session_change():
                session_id = st.session_state["session_selector"]
                # Only reload if the session has actually changed
                if "current_session_id" not in st.session_state or st.session_state.current_session_id != session_id:
                    st.session_state.current_session_id = session_id
                    st.session_state.messages = []
                    history = get_chat_messages(session_id)
                    for sender, message, timestamp in history:
                        st.session_state.messages.append({"role": sender, "content": message})

            # Use selectbox for session selection
            selected_session_id = st.selectbox(
                "Select a session:",
                options=[s[0] for s in sessions],
                format_func=lambda x: next((f"Session {s[0]} - {s[2].split(' ')[0]} ({s[1]})" if s[1] else f"Session {s[0]} - {s[2].split(' ')[0]}" for s in sessions if s[0] == x), str(x)),
                key="session_selector",
                on_change=on_session_change
            )

            if selected_session_id:
                st.markdown(f"**Current Session:** {next((s[1] if s[1] else f'Session {s[0]}') for s in sessions if s[0] == selected_session_id)}")
                new_session_name = st.text_input("Rename session:", value=next((s[1] if s[1] else '') for s in sessions if s[0] == selected_session_id), key="rename_session_input")
                if st.button("Rename Session"): 
                    if new_session_name and new_session_name != next((s[1] if s[1] else '') for s in sessions if s[0] == selected_session_id):
                        update_chat_session_name(selected_session_id, new_session_name)
                        st.success(f"Session {selected_session_id} renamed to '{new_session_name}'.")
                        st.rerun()
                    else:
                        st.warning("Please enter a new name to rename the session.")

                # Add a delete session button
                if st.button("Delete Selected Session"): 
                    delete_chat_session(selected_session_id)
                    st.session_state.messages = []
                    if "current_session_id" in st.session_state:
                        del st.session_state.current_session_id
                    st.success(f"Session {selected_session_id} deleted.")
                    st.rerun()
            else:
                st.warning("Please select a session to delete.")
        else:
            st.info("No chat sessions found. Start a new one!")

    # Add a clear chat button for the current session
    if "current_session_id" in st.session_state and st.session_state.messages:
        if st.button("Clear Current Chat"): 
            clear_chat_messages(st.session_state.current_session_id)
            st.session_state.messages = []
            st.success("Chat history cleared for this session.")
            st.rerun()

    # --- Main Chat Interface ---
    st.title("🤖 Matrix Oracle Interface")
    
    if "current_session_id" in st.session_state:
        # Display chat messages from history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Accept user input
        if query := st.chat_input("Ask the Oracle..."):
            # Add and display user message
            st.session_state.messages.append({"role": "user", "content": query})
            add_chat_message(st.session_state.current_session_id, "user", query)
            with st.chat_message("user"):
                st.markdown(query)

            # Get and display assistant response
            with st.chat_message("assistant"):
                with st.spinner("Oracle is thinking..."):
                    try:
                        full_response = google_chat_service.get_chat_response(context="", question=query)
                    except Exception as e:
                        full_response = f"An error occurred: {e}"
                
                st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                add_chat_message(st.session_state.current_session_id, "assistant", full_response)
    else:
        # Welcome message when no session is selected
        st.info("⬅️ Create a new chat or select an existing one from the sidebar to get started!")

def render_profile_page():
    """Render the user profile page."""
    st.title("User Profile")

    user_id = st.session_state.user_id
    current_username, current_full_name, current_dob, current_email, current_profile_pic_path = get_user_profile(user_id)

    with st.form("profile_form"):
        st.subheader("Update Your Profile")
        new_username = st.text_input("Username", value=current_username)
        new_full_name = st.text_input("Full Name", value=current_full_name if current_full_name else "")
        new_dob = st.text_input("Date of Birth (YYYY-MM-DD)", value=current_dob if current_dob else "")
        new_email = st.text_input("Email", value=current_email if current_email else "")
        new_profile_pic_path = st.text_input("Profile Picture URL/Path", value=current_profile_pic_path if current_profile_pic_path else "")
        new_password = st.text_input("New Password (leave blank to keep current)", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")

        submitted = st.form_submit_button("Update Profile")

        if submitted:
            if new_password and new_password != confirm_password:
                st.error("New password and confirmation do not match.")
            else:
                update_user_profile(
                    user_id,
                    new_username=new_username if new_username != current_username else None,
                    new_password=new_password if new_password else None,
                    new_full_name=new_full_name if new_full_name != current_full_name else None,
                    new_dob=new_dob if new_dob != current_dob else None,
                    new_email=new_email if new_email != current_email else None,
                    new_profile_pic_path=new_profile_pic_path if new_profile_pic_path != current_profile_pic_path else None
                )
                st.success("Profile updated successfully!")
                st.session_state.username = new_username # Update session state if username changed
                st.rerun()

    if st.button("Back to Chat"): # Add a back button
        st.session_state.current_view = "chat"
        st.rerun()

# --- Main Application Logic ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_view" not in st.session_state:
    st.session_state.current_view = "chat" # Default view

if st.session_state.logged_in:
    if st.session_state.current_view == "chat":
        render_main_app()
    elif st.session_state.current_view == "profile":
        render_profile_page()
else:
    render_login_page()