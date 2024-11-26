import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime

# Initialize SQLite database connection
db_path = "data.db"  # Ensure the path matches the one in the chatbot script
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Function to load student data from SQLite
def load_student_data():
    cursor.execute("SELECT * FROM student_data")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    data = [dict(zip(columns, row)) for row in rows]
    return data

# Function to load conversation data from SQLite
def load_conversation_data():
    cursor.execute("SELECT * FROM student_conversations")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    data = [dict(zip(columns, row)) for row in rows]
    return data

# Display Tutor UI
def display_tutor_ui():
    st.title("📋 Tutor Dashboard")
    
    # Load student data and conversation logs
    student_data = load_student_data()
    conversation_data = load_conversation_data()

    # Process student data for display
    table_data = []
    for entry in student_data:
        table_data.append({
            "ID": entry["id"],
            "Student": entry["username"],
            "Timestamp": entry["timestamp"],
            "Grade": entry["grade"],
            "Questions": entry["questions"],
            "Feedback": entry["feedback"]
        })

    # Convert table data to a DataFrame and sort by timestamp
    df = pd.DataFrame(table_data)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    df = df.sort_values(by=['Timestamp'], ascending=False)

    # Toggle button for showing only the top 5 rows
    show_top_5 = st.checkbox("Show Only Top 5 Rows (Unfiltered Data)", value=True)

    # Create a search bar
    search_query = st.text_input("Search student data by student name, grade, or ID", "").strip().lower()

    # Apply search filters
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

    # Data for display
    if search_query:
        display_df = pd.DataFrame(filtered_data)
    else:
        display_df = df if not show_top_5 else df.head(5)

    # Display unified table
    st.write("### Student Data (for best viewing, download and top left align):")
    st.dataframe(display_df[['ID', 'Student', 'Timestamp', 'Grade', 'Questions', 'Feedback']], width=1000, height=400)

    # Add conversation finder
    st.write("### Conversation Finder:")
    conversation_search_id = st.text_input("Search conversation logs by ID", "").strip()

    # Check if the ID exists in conversation data to pull up conversation log
    if conversation_search_id:
        matching_logs = [
            entry for entry in conversation_data if str(entry['id']) == conversation_search_id
        ]

        if matching_logs:
            log = matching_logs[0]
            st.write(f"### Conversation Log for ID {log['id']} - {log['username']} ({log['timestamp']}):")
            for message in log["messages"].split("\n"):
                if message.startswith("user:"):
                    role = "User"
                    content = message[5:]
                elif message.startswith("assistant:"):
                    role = "Assistant"
                    content = message[10:]
                else:
                    continue
                st.write(f"**{role}:** {content}")
        else:
            st.write("No conversation log found for the given ID.")

# Run the UI
if __name__ == "__main__":
    display_tutor_ui()
