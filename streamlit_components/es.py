import os
import streamlit as st
import json


def save_conversation(es_client, timestamp_function):
    if st.button("Save Conversation"):
        st.session_state.show_save_popup = True

    if st.session_state.get('show_save_popup', False):
        with st.form(key='save_form'):
            save_name = st.text_input("Enter a name for this conversation:")
            submit_button = st.form_submit_button(label='Save')
            
            if submit_button and save_name:
                conversation_data = {
                    "name": save_name,
                    "messages": st.session_state.messages,
                    "timestamp": timestamp_function()
                }
                
                try:
                    es_client.index(index="conversations", body=json.dumps(conversation_data))
                    st.success(f"Conversation saved as '{save_name}'")
                except Exception as e:
                    st.error(f"Failed to save conversation: {str(e)}")
                
                st.session_state.show_save_popup = False
                st.rerun()

def load_conversation(es_client):
    # Load button and popup
    if st.button("Load Conversation"):
        st.session_state.show_load_popup = True

    if st.session_state.get('show_load_popup', False):
        try:
            # Fetch all conversations from Elasticsearch
            if es_client.indices.exists(index=os.environ.get("ELASTIC_CONVO_INDEX_NAME")):
                result = es_client.search(index=os.environ.get("ELASTIC_CONVO_INDEX_NAME"), body={"query": {"match_all": {}}, "size": 100})
                conversations = result['hits']['hits']

                if conversations:
                    options = []
                    for conv in conversations:
                        name = conv['_source']['name']
                        timestamp = conv['_source']['timestamp']
                        options.append(f"{name} - {timestamp}")

                    selected_conversation = st.selectbox("Select a conversation to load:", options)

                    if st.button("Load Selected Conversation"):
                        # Find the selected conversation in the results
                        for conv in conversations:
                            if f"{conv['_source']['name']} - {conv['_source']['timestamp']}" == selected_conversation:
                                st.session_state.messages = conv['_source']['messages']
                                st.success(f"Loaded conversation: {selected_conversation}")
                                st.session_state.show_load_popup = False
                                st.rerun()
                                break
                else:
                    st.info("No saved conversations found.")
            else:
                st.info(f"The index {os.environ.get("ELASTIC_CONVO_INDEX_NAME")} doesn't exist. Saving a conversation will create it.")

        except Exception as e:
            st.error(f"Failed to load conversations: {str(e)}")

        if st.button("Close"):
            st.session_state.show_load_popup = False
            st.rerun()


def save_conversation(es_client, timestamp_function):
    if st.button("Save Conversation"):
        st.session_state.show_save_popup = True

    if st.session_state.get('show_save_popup', False):
        with st.form(key='save_form'):
            save_name = st.text_input("Enter a name for this conversation:")
            submit_button = st.form_submit_button(label='Save')
            
            if submit_button and save_name:
                conversation_data = {
                    "name": save_name,
                    "messages": st.session_state.messages,
                    "timestamp": timestamp_function()
                }
                
                try:
                    es_client.index(index="conversations", body=json.dumps(conversation_data))
                    st.success(f"Conversation saved as '{save_name}'")
                except Exception as e:
                    st.error(f"Failed to save conversation: {str(e)}")
                
                st.session_state.show_save_popup = False
                st.rerun()