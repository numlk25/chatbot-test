import streamlit as st
from openai import OpenAI
import json
import os
from datetime import datetime

openai_api_key = st.secrets["openai"]["api_key"]  # fetch API key from Streamlit secrets
client = OpenAI(api_key=openai_api_key)

# function for loading text files
def load_file(filename):
    with open(filename, "r") as file:
        return file.read()

# load files for context and grading criteria
interviewee_context = load_file("context.txt")
grading_criteria = load_file("grading_criteria.txt")

def get_next_id(file_path):
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            if not data:
                return 0  # start with ID 0 if the file is empty
            # get the maximum ID, add 1
            max_id = max(entry.get("id", 0) for entry in data)
            return max_id + 1
    except (FileNotFoundError, json.JSONDecodeError):
        return 0  #start with ID 0 if file is missing or corrupt



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
        content = getattr(chunk.choices[0].delta, 'content', '') or ''
        feedback_response += content

    # Use string methods to find and extract the grade
    grade_marker = "Grade:"
    grade_start = feedback_response.find(grade_marker)  # Find where "Grade:" appears

    if grade_start != -1:  # Ensure "Grade:" was found
        grade_start += len(grade_marker)  # Move the pointer to after "Grade:"
        grade = feedback_response[grade_start:grade_start+2].strip()  # Extract 1 or 2 characters and trim whitespace
        feedback_response = feedback_response[:grade_start-len(grade_marker)].strip()  # Remove the grade from the feedback
    else:
        grade = "Grade not found, please review manually."

    # Return the feedback without the grade, but store the grade internally
    return feedback_response, grade



def save_student_data(username, grade, questions, feedback):
    # Define file path
    file_path = "student_data.json"
    
    # Generate the next unique ID
    new_id = get_next_id(file_path)

    # Create a data structure for the new entry, including ID and feedback
    new_entry = {
        "id": new_id,
        "username": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "grade": grade,
        "questions": questions,
        "feedback": feedback
    }
    
    # Load existing data and append the new entry
    with open(file_path, "r+") as file:
        try:
            current_data = json.load(file)  # Load current JSON data
        except json.JSONDecodeError:
            current_data = []  # Start fresh if the file is empty or corrupt

        current_data.append(new_entry)  # Append new student data
        file.seek(0)  # Move to the start of the file
        json.dump(current_data, file, indent=4)  # Write updated data




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

    st.title("📋 Interview Practice Chatbot")
    st.write(
        "This is an interview practice chatbot where you can ask questions related to the manufacturing process. "
        "You will receive feedback on your performance at the end of the conversation."
    )



    conversation_file = "student_conversations.json"



    """Conversation functions"""

    # Load user-specific conversations on startup
    def load_conversations(username):
        try:
            with open(conversation_file, "r") as file:
                conversations = json.load(file)
            return [conv for conv in conversations if conv["username"] == username]
        except (FileNotFoundError, json.JSONDecodeError):
            return []  # Return an empty list if the file is missing or corrupt

    def save_conversation(username, conversation):
        """Save the filtered conversation to a file."""
        # Define file path
        file_path = "student_conversations.json"
        
        # Generate the next unique ID
        new_id = get_next_id(file_path)

        # Filter out system messages from the conversation
        filtered_conversation = [msg for msg in conversation if msg["role"] != "system"]

        # Create a new conversation entry with a unique ID
        new_entry = {
            "id": new_id,
            "username": username,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "messages": filtered_conversation  # Save only filtered messages
        }
        
        try:
            with open(file_path, "r+") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    data = []  # Initialize empty list if file is empty or corrupted

                data.append(new_entry)
                file.seek(0)
                json.dump(data, file, indent=4)
        except FileNotFoundError:
            with open(file_path, "w") as file:
                json.dump([new_entry], file, indent=4)


    def reset_conversation():
        """Reset session state for starting a new conversation."""
        st.session_state.messages = [
            {"role": "system", "content": interviewee_context},  # Hidden system message
            {"role": "assistant", "content": "Hi, I'm here to help you with questions about the manufacturing process."}
        ]
        st.session_state.user_questions = []
        st.session_state.conversation_ended = False



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



    # Load user's conversations on app load
    st.session_state.conversations = load_conversations(st.session_state.username)



    # Sidebar: Display previous conversations
    st.sidebar.title(f"{st.session_state.username}'s Past Conversations")
    if st.session_state.conversations:
        for idx, conv in enumerate(st.session_state.conversations):
            if st.sidebar.button(f"Load Conversation {idx + 1}"):
                # Set review mode
                st.session_state.is_review_mode = True
                st.session_state.messages = conv["messages"]
                st.session_state.conversation_ended = True  # Ensure conversation is treated as ended
                st.session_state.user_questions = [msg["content"] for msg in conv["messages"] if msg["role"] == "user"]

    # Reset review mode when starting a new conversation
    if st.button("🔥 Start New Conversation (remember to save your conversations!)"):
        reset_conversation()
        st.session_state.is_review_mode = False  # Allow editing for new conversation

    # Display current conversation
    for message in st.session_state.messages:
        if message["role"] != "system":  # Skip displaying the system message
            role = "assistant" if message["role"] == "assistant" else "user"
            st.chat_message(role).markdown(message["content"])

    # Disable inputs in review mode
    if not st.session_state.conversation_ended or not st.session_state.is_review_mode:
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

    # Handle conversation end and saving to file
    if st.button("Save and End Conversation") and not st.session_state.conversation_ended and not st.session_state.is_review_mode:
        st.markdown("### Analyzing your performance...")
        st.session_state.conversation_ended = True
        feedback, grade = evaluate_performance(st.session_state.user_questions)
        save_conversation(st.session_state.username, st.session_state.messages)
        save_student_data(st.session_state.username, grade, st.session_state.user_questions, feedback)  # Pass feedback to save
        st.markdown(f"**Feedback:** {feedback.strip()}")
        st.stop()
