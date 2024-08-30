import streamlit as st
import os
from elasticsearch import Elasticsearch
from prompts import prompts
from AzureOpenAIClient import AzureOpenAIClient
from utils import get_current_time, count_words_in_conversation, create_conversational_prompt
from dotenv import load_dotenv
import json
load_dotenv()

# Elasticsearch setup
es_endpoint = f"https://{os.environ.get('ELASTIC_CLUSTER_ID')}.{os.environ.get('ELASTIC_CLUSTER_HOST')}"
es_client = Elasticsearch(
    es_endpoint,
    api_key=os.environ.get("ELASTIC_API_KEY")
)

LLM = AzureOpenAIClient()

st.set_page_config(layout="wide")

main_content, padding, right_options = st.columns([3, 0.15, 1])

# LEFT SIDEBAR
st.sidebar.title("Chat Settings")

model = st.sidebar.radio(
    "Select LLM",
    ("gpt-4o", "gpt-4o-mini"),
    index=0
)

system_prompt = st.sidebar.radio(
    "Select System Prompt",
    (i for i in list(prompts.keys())),
    index=0  
)

total_word_count = count_words_in_conversation(st.session_state.get('messages', []), len(st.session_state.get('messages', [])))

conversation_length = st.sidebar.slider("Conversation History Length", min_value=1, max_value=20, value=10, step=1)

word_count = count_words_in_conversation(st.session_state.get('messages', []), conversation_length)
st.sidebar.markdown(f"""
    Words in selected history: 
    <p style='font-size:28px; font-weight:bold; color:#4CAF50; background-color:#E8F5E9; padding:5px 10px; border-radius:2px; display:inline-block;'>{word_count}</p>
    """, unsafe_allow_html=True)

st.sidebar.markdown(f"""
    Total words in conversation: 
    <p style='font-size:28px; font-weight:bold; color:#2196F3; background-color:#E3F2FD; padding:5px 10px; border-radius:2px; display:inline-block;'>{total_word_count}</p>
    """, unsafe_allow_html=True)

# RIGHT SIDEBAR
with right_options:
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

    es_connected = es_client.ping()
    es_health = es_client.cluster.health()
    st.markdown(f"**Elasticsearch Endpoint:** {es_endpoint}")
    if es_connected:
        st.markdown('<p style="background-color:#CCFFCC; color:#007700; padding:10px; border-radius:5px;"><strong>Connected to Elasticsearch Cluster</strong></p>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="background-color:#FFCCCC; color:#CC0000; padding:10px; border-radius:5px;"><strong>Failed to connect to Elasticsearch Cluster</strong></p>', unsafe_allow_html=True)

    # Save button and popup
    if st.button("Save Conversation"):
        st.session_state.show_popup = True

    if st.session_state.get('show_popup', False):
        with st.form(key='save_form'):
            save_name = st.text_input("Enter a name for this conversation:")
            submit_button = st.form_submit_button(label='Save')
            
            if submit_button and save_name:
                # Save conversation to Elasticsearch
                conversation_data = {
                    "name": save_name,
                    "messages": st.session_state.messages,
                    "timestamp": get_current_time()
                }
                
                try:
                    es_client.index(index="conversations", body=json.dumps(conversation_data))
                    st.success(f"Conversation saved as '{save_name}'")
                except Exception as e:
                    st.error(f"Failed to save conversation: {str(e)}")
                
                st.session_state.show_popup = False
                st.rerun()

# CHAT WINDOW 
with main_content:
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(f"{message['content']}")
            st.caption(f"Sent at {message['time']}")

    if prompt := st.chat_input("Start Chatting!"):
        with st.chat_message("user"):
            st.markdown(prompt)
            st.caption(f"Sent at {get_current_time()}")
        st.session_state.messages.append({"role": "user", "content": prompt, "time": get_current_time()})

        with st.spinner("Generating Response..."):
            conversation_prompt = create_conversational_prompt(st.session_state.messages, conversation_length=conversation_length)
            assistant_response = LLM.generate_streaming_response(conversation_prompt, model=model, system_prompt=prompts[system_prompt])

        st.session_state.messages.append({"role": "assistant", "content": assistant_response, "time": get_current_time()})
        st.rerun()