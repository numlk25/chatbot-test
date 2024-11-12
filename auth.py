import streamlit as st
import json

# Path to the JSON file
users_file = "users.json"

def load_users(file_path):
    """Load user data from a JSON file."""
    try:
        with open(file_path, "r") as f:
            users = json.load(f)
    except FileNotFoundError:
        st.error("User data file not found.")
        return {}
    except json.JSONDecodeError:
        st.error("Error reading user data.")
        return {}
    return users

def login():
    if "username" not in st.session_state:
        st.session_state.username = None

    if st.session_state.username is None:
        st.title("Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")

            if submit_button:
                users = load_users(users_file)  # Load users from JSON file
                if username in users and users[username] == password:
                    st.session_state.username = username
                    st.success(f"Logged in as {username}")
                    return True
                else:
                    st.error("Invalid username or password")
                    return False
    return st.session_state.username is not None
