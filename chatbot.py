
import streamlit as st
import sqlite3
from datetime import datetime
from openai import OpenAI
import os
import json

# Initialize SQLite database connection
db_path = "data.db"  # Name of the SQLite database file
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS student_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    timestamp TEXT,
    grade TEXT,
    questions TEXT,
    feedback TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS student_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    timestamp TEXT,
    messages TEXT
)
""")
conn.commit()

# Load API key
openai_api_key = os.getenv("api_key")  # Ensure the key is set in the environment variables
client = OpenAI(api_key=openai_api_key)

# Function to load text files
def load_file(filename):
    with open(filename, "r") as file:
        return file.read()

# Load context and grading criteria
interviewee_context = load_file("context.txt")
grading_criteria = load_file("grading_criteria.txt")

# Helper function to evaluate performance
def evaluate_performance(questions):
    performance_prompt = f"""
    {grading_criteria}

    The following is a list of questions asked by a student during an interview. Evaluate their performance based on their ability to ask good questions. Consider how specific, concise, and thoughtful the questions are.

    Student's questions:
    {questions}
    """

    # Generate feedback from GPT-4
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": performance_prompt}],
        stream=True
    )

    feedback_response = ""  # Initialize an empty string to accumulate feedback

    # Process the streaming response
    for chunk in stream:
        content = getattr(chunk.choices[0].delta, "content", "") or ""
        feedback_response += content

    # Extract grade
    grade_marker = "Grade:"
    grade_start = feedback_response.find(grade_marker)

    if grade_start != -1:
        grade_start += len(grade_marker)
        grade = feedback_response[grade_start:grade_start+2].strip()
        feedback_response = feedback_response[:grade_start-len(grade_marker)].strip()
    else:
        grade = "Grade not found, please review manually."

    return feedback_response, grade

# Function to save student data
def save_student_data(username, grade, questions, feedback):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    questions_text = "\n".join(questions)
    
    cursor.execute("""
    INSERT INTO student_data (username, timestamp, grade, questions, feedback)
    VALUES (?, ?, ?, ?, ?)
    """, (username, timestamp, grade, questions_text, feedback))
    conn.commit()
    st.success("Student data saved successfully!")

# Function to save a conversation
def save_conversation(username, conversation):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filtered_conversation = [msg for msg in conversation if msg["role"] != "system"]
    conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in filtered_conversation])
    
    cursor.execute("""
    INSERT INTO student_conversations (username, timestamp, messages)
    VALUES (?, ?, ?)
    """, (username, timestamp, conversation_text))
    conn.commit()
    st.success("Conversation saved successfully!")

# Function to load previous conversations for a user
def load_conversations(username):
    cursor.execute("""
    SELECT messages FROM student_conversations
    WHERE username = ?
    ORDER BY timestamp ASC
    """, (username,))
    results = cursor.fetchall()
    conversations = [
        [{"role": "user" if line.startswith("user:") else "assistant", 
          "content": line.split(": ", 1)[1]} 
         for line in result[0].split("\n")]
        for result in results
    ]
    return conversations

# Function to reset conversation
def reset_conversation():
    st.session_state.messages = [
        {"role": "system", "content": interviewee_context},
        {"role": "assistant", "content": "Hi, I'm here to help you with questions about the manufacturing process."}
    ]
    st.session_state.user_questions = []
    st.session_state.conversation_ended = False

# Chatbot page
def chatbot_page():
    # Initialize session state attributes
    if "conversations" not in st.session_state:
        st.session_state.conversations = []

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": interviewee_context},
            {"role": "assistant", "content": "Hi, I'm here to help you with questions about the manufacturing process."}
        ]

    if "user_questions" not in st.session_state:
        st.session_state.user_questions = []

    if "username" not in st.session_state:
        st.session_state.username = "guest"

    if "conversation_ended" not in st.session_state:
        st.session_state.conversation_ended = False

    if "is_review_mode" not in st.session_state:
        st.session_state.is_review_mode = False

    st.title("📋 Interview Practice Chatbot")
    st.write(
        "This is an interview practice chatbot where you can ask questions related to the manufacturing process. "
        "You will receive feedback on your performance at the end of the conversation."
    )

    # Load user's conversations on app load
    st.session_state.conversations = load_conversations(st.session_state.username)

    # Sidebar: Display previous conversations
    st.sidebar.title(f"{st.session_state.username}'s Past Conversations")
    if st.session_state.conversations:
        for idx, conv in enumerate(st.session_state.conversations):
            if st.sidebar.button(f"Load Conversation {idx + 1}"):
                st.session_state.is_review_mode = True
                st.session_state.messages = conv
                st.session_state.conversation_ended = True
                st.session_state.user_questions = [msg["content"] for msg in conv if msg["role"] == "user"]

    # Reset review mode when starting a new conversation
    if st.button("🔥 Start New Conversation (remember to save your conversations!)"):
        reset_conversation()
        st.session_state.is_review_mode = False

    # Display current conversation
    for message in st.session_state.messages:
        if message["role"] != "system":
            role = "assistant" if message["role"] == "assistant" else "user"
            st.chat_message(role).markdown(message["content"])

    # Chat input and assistant response
    if not st.session_state.conversation_ended and not st.session_state.is_review_mode:
        if user_input := st.chat_input("Ask a question about the manufacturing process:", key="user_input"):
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.user_questions.append(user_input)
            st.chat_message("user").markdown(user_input)

            # Chat model response
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages,
                stream=True
            )

            assistant_response = ""
            for chunk in stream:
                content = getattr(chunk.choices[0].delta, "content", "") or ""
                assistant_response += content

            st.chat_message("assistant").markdown(assistant_response)
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    else:
        st.write("This is a previously saved conversation and cannot be edited.")

    # Handle conversation end and saving
    if st.button("Save and End Conversation") and not st.session_state.conversation_ended and not st.session_state.is_review_mode:
        st.markdown("### Analyzing your performance...")
        st.session_state.conversation_ended = True
        feedback, grade = evaluate_performance(st.session_state.user_questions)
        save_conversation(st.session_state.username, st.session_state.messages)
        save_student_data(st.session_state.username, grade, st.session_state.user_questions, feedback)
        st.markdown(f"**Feedback:** {feedback.strip()}")
