import streamlit as st
import requests

st.set_page_config(page_title="Chatbot", layout="centered")

# Title
st.title("💬 Chat with AI")

# Fixed user_thread info
USER_THREAD = {
    "user_id": "1234",
    "thread_id": "1234123411",
    "agent_name": "Changpeng Zhao AI"
}


USER_THREAD = {
    "user_id": "1234",
    "thread_id": "1234123411",
    "agent_name": "MISS CHINA AI"
}


# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Function to send user message to API and get response
def get_bot_response(question):
    payload = {
        "user_thread": USER_THREAD,
        "question": question
    }

    try:
        response = requests.post(
            "http://0.0.0.0:8070/ask",
            json=payload,
            timeout=1000  # Increased timeout for skin analysis
        )
        response.raise_for_status()
        json_response = response.json()
        return json_response.get("response", "No response from server.")
    except requests.exceptions.RequestException as e:
        return f"❌ Error: {str(e)}"

# Display chat history
for chat in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(chat["user"])
    with st.chat_message("assistant"):
        st.markdown(chat["bot"], unsafe_allow_html=True)

# User input box
user_input = st.chat_input("Say something...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    bot_response = get_bot_response(user_input)

    with st.chat_message("assistant"):
        st.markdown(bot_response, unsafe_allow_html=True)

    # Save chat history
    st.session_state.chat_history.append({
        "user": user_input,
        "bot": bot_response
    })
