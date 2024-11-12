import json
import streamlit as st

def load_student_data():
    try:
        with open("student_data.json", "r") as file:
            data = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        data = []  # Return an empty list if the file is empty, corrupted, or missing
    return data

def display_tutor_ui():
    st.title("📋 Tutor Dashboard")
    data = load_student_data()

    # Add search and filter options
    search_query = st.text_input("Search by student name or grade", "").strip().lower()
    if search_query:
        data = [entry for entry in data if search_query in entry['username'].lower() or search_query in entry['grade'].lower()]

    if data:
        for index, entry in enumerate(data):
            # Display student information
            st.write(f"**Student:** {entry['username']}")
            st.write(f"**Timestamp:** {entry['timestamp']}")
            st.write(f"**Grade:** {entry['grade']}")

            # Expander for questions
            with st.expander("Questions Asked"):
                for question in entry["questions"]:
                    st.write(f"- {question}")

            # Divider between entries
            if index < len(data) - 1:  # Avoid adding divider after the last entry
                try:
                    st.divider()  # For Streamlit versions that support it
                except AttributeError:
                    st.markdown("<hr style='border: 1px solid #ddd;'>", unsafe_allow_html=True)

    else:
        st.write("No student data available or no results for your search.")

# Display the UI
display_tutor_ui()
