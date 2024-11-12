import streamlit as st
from auth import login
from chatbot import chatbot_page
from tutorui import display_tutor_ui

if "username" not in st.session_state:
    st.session_state.username = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "main"

def go_to_main():
    st.session_state.page = "main"

def go_to_chatbot():
    st.session_state.page = "chatbot"

def go_to_tutorui():
    st.session_state.page = "tutorui"

def logout():
    st.session_state.username = None
    st.session_state.logged_in = False
    st.session_state.page = "main"

if not st.session_state.logged_in:
    st.title("Login Page")
    if login():
        st.session_state.logged_in = True
        st.session_state.username = st.session_state.username or "guest"
        if st.session_state.username == "student":
            go_to_chatbot()
        if st.session_state.username == "tutor":
            go_to_tutorui()
else:
    st.sidebar.button("Logout", on_click=logout)
    if st.session_state.page == "chatbot" and st.session_state.username == "student":
        chatbot_page()
    elif st.session_state.page == "tutorui" and st.session_state.username == "tutor":
        display_tutor_ui()
