import os
import streamlit as st
import requests
import base64
import pandas as pd
from io import BytesIO
from PIL import Image

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "current_chat" not in st.session_state:
    st.session_state.current_chat = {"messages": [], "name": f"Chat {len(st.session_state.chat_history) + 1}"}

def add_new_chat():
    if st.session_state.current_chat["messages"]:
        st.session_state.chat_history.append(st.session_state.current_chat)
    st.session_state.current_chat = {"messages": [], "name": f"Chat {len(st.session_state.chat_history) + 1}"}
    st.experimental_rerun()

def select_chat(index):
    st.session_state.chat_history.append(st.session_state.current_chat)
    st.session_state.current_chat = st.session_state.chat_history.pop(index)
    st.experimental_rerun()

def delete_chat(index):
    st.session_state.chat_history.pop(index)
    for i in range(len(st.session_state.chat_history)):
        st.session_state.chat_history[i]["name"] = f"Chat {i + 1}"

def rename_chat(index, new_name):
    st.session_state.chat_history[index]["name"] = new_name

# Custom CSS for expanding the sidebar
st.markdown(
    """
    <style>
        .sidebar .sidebar-content {
            position: relative;
            width: 60px;
            transition: width 0.3s;
        }
        .sidebar:hover .sidebar-content {
            width: 400px;
        }
        .sidebar .sidebar-content {
            overflow: hidden;
        }
        .sidebar:hover .sidebar-content {
            overflow: auto;
        }
        .chat-element {
            padding: 5px;
            margin-bottom: 5px;
            background-color: #f0f0f0;
            border-radius: 5px;
        }
        .current-chat {
            font-weight: bold;
            color: green;
        }
        .chat-info {
            margin-left: 10px;
            font-size: 0.9rem;
            color: #333;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar for chat history
with st.sidebar:
    st.title("Chat History")
    col1, col2 = st.columns([3, 3])
    with col1:
        if st.button("New Chat"):
            add_new_chat()
    with col2:
        st.write("")  # Empty space to align "Current Chat" with the button

    st.markdown(f"<div class='chat-info'>Current Chat: <span class='current-chat'>{st.session_state.current_chat['name']}</span></div>", unsafe_allow_html=True)

    for i, chat in enumerate(st.session_state.chat_history):
        with st.container():
            expander_text = chat['name']
            if chat['name'] == st.session_state.current_chat['name']:  # Mark the current chat
                expander_text += " (in use)"
                is_current_chat = True
            else:
                is_current_chat = False
            
            with st.expander(expander_text, expanded=is_current_chat):
                if st.button(f"Select {chat['name']}", key=f"select_{i}"):
                    select_chat(i)
                    st.experimental_rerun()
                if st.button(f"Delete {chat['name']}", key=f"delete_{i}"):
                    delete_chat(i)
                    st.experimental_rerun()
                new_name = st.text_input(f"Rename {chat['name']}", chat['name'], key=f"rename_{i}")
                if st.button(f"Rename {chat['name']}", key=f"rename_button_{i}"):
                    rename_chat(i, new_name)
                    st.experimental_rerun()

# Main App Title with current chat name
st.title(f"Streamlit for Sales Usecase - {st.session_state.current_chat['name']}")
st.write("This is a Streamlit app for the Sales Usecase.")

# Display chat history
for message in st.session_state.current_chat["messages"]:
    if "role" in message and "type" in message and "content" in message:  # Ensure keys are present
        with st.chat_message(message["role"]):
            if message["type"] == "text":
                st.markdown(message["content"])
            elif message["type"] == "image":
                img_data = message["content"].split(",")[1]
                img = Image.open(BytesIO(base64.b64decode(img_data)))
                st.image(img)
            elif message["type"] == "table":
                table_df = pd.read_json(BytesIO(message["content"].encode("utf-8")))
                st.table(table_df)
            elif message["type"] == "json":
                try:
                    json_data = pd.read_json(BytesIO(message["content"].encode("utf-8")))
                    st.json(json_data)
                except ValueError:
                    st.json(message["content"])

# Input for new message
if prompt := st.chat_input("Type something..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.current_chat["messages"].append({"role": "user", "type": "text", "content": prompt})
    
    # Get response from the backend
    request_url = "https://dbbackend001.azurewebsites.net/ask"
    try:
        response = requests.post(request_url, json={"question": prompt}).json()
        if 'error' in response:
            st.error(response['error'])
            st.session_state.current_chat["messages"].append({"role": "bot", "type": "text", "content": response['error']})
        else:
            notebook_response = response[0].get("notebook_output", {}).get("result", "")
            if notebook_response.startswith("data:image"):
                img_data = notebook_response.split(",")[1]
                img = Image.open(BytesIO(base64.b64decode(img_data)))
                st.image(img)
                st.session_state.current_chat["messages"].append({"role": "bot", "type": "image", "content": notebook_response})
            elif notebook_response.startswith("{") or notebook_response.startswith("["):
                try:
                    response_data = pd.read_json(BytesIO(notebook_response.encode("utf-8")))
                    st.table(response_data)
                    st.session_state.current_chat["messages"].append({"role": "bot", "type": "table", "content": notebook_response})
                except ValueError:
                    st.json(notebook_response)
                    st.session_state.current_chat["messages"].append({"role": "bot", "type": "json", "content": notebook_response})
            else:
                st.markdown(notebook_response)
                st.session_state.current_chat["messages"].append({"role": "bot", "type": "text", "content": notebook_response})
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.session_state.current_chat["messages"].append({"role": "bot", "type": "text", "content": "An error occurred while processing your request."})
