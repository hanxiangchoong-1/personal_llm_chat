import streamlit as st
import os
from elasticsearch import Elasticsearch
from prompts import prompts
from AzureOpenAIClient import AzureOpenAIClient
from utils import get_current_time, count_words_in_conversation, create_conversational_prompt
from streamlit_components.es import save_conversation, load_conversation, get_elasticsearch_results, create_RAG_context, get_valid_indices
from dotenv import load_dotenv
import json
from datetime import datetime
load_dotenv()


# Elasticsearch setup
es_endpoint = os.environ.get("ELASTIC_ENDPOINT")
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

conversation_length = st.sidebar.slider("Conversation History Length", min_value=1, max_value=30, value=10, step=1)

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
selected_indices=[]
with right_options:
    st.title("Elasticsearch")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

    es_connected=False
    # TRY TO DISPLAY ERROR MESSAGE IF CONNECTION FAILS
    try:
        es_connected = es_client.ping()
        es_health = es_client.cluster.health()
    except Exception as e: 
        es_health='FAILURE'
    st.markdown(f"**Cluster Endpoint:** {es_endpoint}")
    if es_connected:
        st.markdown('<p style="background-color:#CCFFCC; color:#007700; padding:10px; border-radius:5px;"><strong>Connected to Elasticsearch Cluster</strong></p>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="background-color:#FFCCCC; color:#CC0000; padding:10px; border-radius:5px;"><strong>Failed to connect to Elasticsearch Cluster</strong></p>', unsafe_allow_html=True)

    # Elastic Search Components
    save_conversation(es_client, get_current_time)
    load_conversation(es_client)

    # RAG MODE

    rag_mode = st.checkbox("RAG Mode")
    
    if rag_mode:
        # Define the list of valid indices
        valid_index_list = [
            "standard_chartered_half_year_2024",
            "standard_chartered_news_releases_2023_2024",
            # Add more indices as needed
        ]
        
        # Get list of valid indices that exist and have documents
        valid_indices = get_valid_indices(es_client, valid_index_list)
        
        if valid_indices:
            selected_indices = st.multiselect("Select Elasticsearch Indices", valid_indices)
            es_size = st.slider("Elasticsearch Result Size", min_value=1, max_value=20, value=10, step=1)
        else:
            st.warning("No valid indices found. RAG mode is disabled.")
            rag_mode = False


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

        with st.spinner("Generating Response..."):
            
            if rag_mode and selected_indices:
                # RAG mode
                elasticsearch_results = get_elasticsearch_results(es_client, prompt, selected_indices, es_size)
                RAG_context = create_RAG_context(elasticsearch_results, prompt)
                st.session_state.messages.append({"role": "user", "content": prompt, "RAG_context": RAG_context, "time": get_current_time()})
            else:
                st.session_state.messages.append({"role": "user", "content": prompt, "RAG_context": "", "time": get_current_time()})
                
            conversation_prompt = create_conversational_prompt(st.session_state.messages, conversation_length=conversation_length)

            assistant_response = LLM.generate_streaming_response(conversation_prompt, model=model, system_prompt=prompts[system_prompt])

        st.session_state.messages.append({"role": "assistant", "content": assistant_response, "RAG_context": "", "time": get_current_time()})
        st.rerun()