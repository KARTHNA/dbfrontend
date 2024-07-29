import streamlit as st
import requests
import base64
import pandas as pd
from io import BytesIO
from PIL import Image

st.title('Streamlit for Sales Usecase')
st.write('This is a Streamlit app for the Sales Usecase.')

# Streamlit Chatbox
request_url = "https://dbbackend001.azurewebsites.net/ask"

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["type"] == "text":
            st.markdown(message["content"])
        elif message["type"] == "image":
            img_data = message["content"].split(",")[1]
            img = Image.open(BytesIO(base64.b64decode(img_data)))
            st.image(img)
        elif message["type"] == "table":
            table_df = pd.read_json(BytesIO(message["content"].encode('utf-8')))
            st.table(table_df)
        elif message["type"] == "json":
            try:
                json_data = pd.read_json(BytesIO(message["content"].encode('utf-8')))
                st.json(json_data)
            except ValueError:
                st.json(message["content"])

if prompt := st.chat_input("Type something..."):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "type": "text", "content": prompt})
    
    # Get response from the backend
    try:
        response = requests.post(request_url, json={"question": prompt}).json()
        # Check if the response contains 'error'
        if 'error' in response:
            st.error(response['error'])
            st.session_state.messages.append({"role": "bot", "type": "text", "content": response['error']})
        else:
            notebook_response = response[0].get("notebook_output", {}).get("result", "")

            # Display bot response in chat message container
            # Check if the response is a base64 string (assume image if it starts with 'data:image')
            if notebook_response.startswith("data:image"):
                img_data = notebook_response.split(",")[1]
                img = Image.open(BytesIO(base64.b64decode(img_data)))
                st.image(img)
                st.session_state.messages.append({"role": "bot", "type": "image", "content": notebook_response})
            # Check if the response is JSON data (assume table if it starts with '{' or '[')
            elif notebook_response.startswith("{") or notebook_response.startswith("["):
                try:
                    response_data = pd.read_json(BytesIO(notebook_response.encode('utf-8')))
                    st.table(response_data)
                    st.session_state.messages.append({"role": "bot", "type": "table", "content": notebook_response})
                except ValueError:
                    # Handle the case where JSON is not in table format
                    st.json(notebook_response)
                    st.session_state.messages.append({"role": "bot", "type": "json", "content": notebook_response})
            else:
                st.markdown(notebook_response)
                st.session_state.messages.append({"role": "bot", "type": "text", "content": notebook_response})
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.session_state.messages.append({"role": "bot", "type": "text", "content": "An error occurred while processing your request."})
