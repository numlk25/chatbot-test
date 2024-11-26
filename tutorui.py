import json
import streamlit as st
import pandas as pd
from datetime import datetime

def load_student_data():
    try:
        with open("student_data.json", "r") as file:
            data = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        data = []  # return an empty list if the file is empty, corrupted, or missing
    return data

def load_conversation_data():
    try:
        with open("student_conversations.json", "r") as file:
            data = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        data = []  # same thing
    return data

def display_tutor_ui():
    st.title("📋 Tutor Dashboard")
    
    # load student data and conversation logs
    student_data = load_student_data()
    conversation_data = load_conversation_data()

    # process student data for initial display
    table_data = []
    for entry in student_data:
        questions_str = "\n\n".join(entry["questions"])
        feedback_str = entry.get("feedback", "No feedback provided")

        table_data.append({
            "ID": entry.get("id", "N/A"),
            "Student": entry['username'],
            "Timestamp": entry['timestamp'],
            "Grade": entry['grade'],
            "Questions": questions_str,
            "Feedback": feedback_str
        })

    # convert table data to a DataFrame and sort by timestamp (technically same as ID)
    df = pd.DataFrame(table_data)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    df = df.sort_values(by=['Timestamp'], ascending=False)

    # toggle button for showing only the top 5 rows
    show_top_5 = st.checkbox("Show Only Top 5 Rows (Unfiltered Data)", value=True)

# Create a search bar
search_query = st.text_input("Search student data by student name, grade, or ID", "").strip().lower()

# Apply search filters and grade logic
filtered_data = [
    entry for entry in table_data
    if (
        # Check if the query is a grade ("a", "b", "c", "d") and matches the grade
        (len(search_query) == 1 and search_query in ["a", "b", "c", "d"] 
         and entry['Grade'].lower() == search_query)
        or
        # Otherwise, treat the query as a student name or ID
        (
            len(search_query) > 1
            or search_query not in ["a", "b", "c", "d"]
        )
        and (
            search_query in entry['Student'].lower() 
            or search_query in str(entry['ID']).lower()
        )
    )
    # Exclude entries with "Grade not found, please review manually"
    and entry['Grade'].lower() != "grade not found, please review manually"
]

    # data for display
    if search_query:
        display_df = pd.DataFrame(filtered_data)
    else:
        display_df = df if not show_top_5 else df.head(5)

    # display unified table
    st.write("### Student Data (for best viewing, download and top left align):")
    st.dataframe(display_df[['ID', 'Student', 'Timestamp', 'Grade', 'Questions', 'Feedback']], width=1000, height=400)

    # add conversation finder
    st.write("### Conversation Finder:")
    conversation_search_id = st.text_input("Search conversation logs by ID", "").strip()

    # check if the ID exists in conversation data to pull up conversation log
    if conversation_search_id:
        matching_logs = [
            entry for entry in conversation_data if str(entry['id']) == conversation_search_id
        ]

        if matching_logs:
            log = matching_logs[0]
            st.write(f"### Conversation Log for ID {log['id']} - {log['username']} ({log['timestamp']}):")
            for message in log["messages"]:
                role = message["role"].capitalize()
                content = message["content"]
                st.write(f"**{role}:** {content}")
        else:
            st.write("No conversation log found for the given ID.")

# display UI
display_tutor_ui()
