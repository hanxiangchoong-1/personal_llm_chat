import streamlit as st
import os
from elasticsearch import Elasticsearch
from prompts import prompts
from AzureOpenAIClient import AzureOpenAIClient
from utils import get_current_time, count_words_in_conversation, create_conversational_prompt
from dotenv import load_dotenv
load_dotenv()



# '''
# SAVE AND UPLOAD CONVERSATIONS TO ELASTIC SEARCH
# '''

es_endpoint=f"https://{os.environ.get("ELASTIC_CLUSTER_ID")}.{os.environ.get("ELASTIC_CLUSTER_HOST")}"
es_client = Elasticsearch(
    es_endpoint,
    api_key=os.environ.get("ELASTIC_API_KEY")

)

LLM=AzureOpenAIClient()


st.set_page_config(layout="wide")

main_content, padding, right_options = st.columns([3, 0.15, 1])  # Adjust the ratio as needed

# LEFT SIDEBAR

# Sidebar for conversation length control
st.sidebar.title("Chat Settings")

# Model selection using radio buttons
model = st.sidebar.radio(
    "Select LLM",
    ("gpt-4o", "gpt-4o-mini"),
    index=0  # Default to GPT-4
)

# Model selection using radio buttons
system_prompt = st.sidebar.radio(
    "Select System Prompt",
    (i for i in list(prompts.keys())),
    index=0  
)


# Calculate total word count
total_word_count = count_words_in_conversation(st.session_state.get('messages', []), len(st.session_state.get('messages', [])))

conversation_length = st.sidebar.slider("Conversation History Length", min_value=1, max_value=20, value=10, step=1)

# Display word count above the slider
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

    es_connected=es_client.ping()
    es_health=es_client.cluster.health()
    st.markdown(f"**Elasticsearch Endpoint:** {es_endpoint}")
    if es_connected:
        st.markdown('<p style="background-color:#CCFFCC; color:#007700; padding:10px; border-radius:5px;"><strong>Connected to Elasticsearch Cluster</strong></p>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="background-color:#FFCCCC; color:#CC0000; padding:10px; border-radius:5px;"><strong>Failed to connect to Elasticsearch Cluster</strong></p>', unsafe_allow_html=True)


# CHAT WINDOW 

with main_content:
    # Initialize chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(f"{message['content']}")
            st.caption(f"Sent at {message['time']}")

    if prompt := st.chat_input("Start Chatting!"):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
            st.caption(f"Sent at {get_current_time()}")
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt, "time": get_current_time()})

        # Process the question through RAG system
        with st.spinner("Generating Response..."):
            conversation_prompt = create_conversational_prompt(st.session_state.messages, conversation_length=conversation_length)
            assistant_response = LLM.generate_streaming_response(conversation_prompt, model=model, system_prompt=prompts[system_prompt])
            
            # print(conversation_prompt)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": assistant_response, "time": get_current_time()})
        # print(st.session_state.messages)
        # Refresh to update the word counter
        st.rerun()