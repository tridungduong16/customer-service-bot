import streamlit as st
import requests

st.set_page_config(page_title="Chatbot", layout="centered")
st.title("💬 Chat with AI")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def get_bot_response(question, history):
    # Combine previous history + new user input into one string
    full_prompt = ""
    for chat in history:
        full_prompt += f"User: {chat['user']}\nAssistant: {chat['bot']}\n"
    full_prompt += f"User: {question}\nAssistant:"

    payload = {
        "question": full_prompt
    }

    try:
        response = requests.post(
            "http://0.0.0.0:8010/ask",
            json=payload,
            timeout=1000
        )
        response.raise_for_status()
        json_response = response.json()
        return json_response.get("response", "No response from server.")
    except requests.exceptions.RequestException as e:
        return f"❌ Error: {str(e)}"

# Show chat history
for chat in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(chat["user"])
    with st.chat_message("assistant"):
        st.markdown(chat["bot"], unsafe_allow_html=True)

# Chat input
user_input = st.chat_input("Say something...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    bot_response = get_bot_response(user_input, st.session_state.chat_history)

    with st.chat_message("assistant"):
        st.markdown(bot_response, unsafe_allow_html=True)

    st.session_state.chat_history.append({
        "user": user_input,
        "bot": bot_response
    })
