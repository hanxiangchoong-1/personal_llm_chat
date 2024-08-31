import os
import streamlit as st
import json


def save_conversation(es_client, timestamp_function):
    if st.button("Save Conversation"):
        st.session_state.show_save_popup = True

        print(os.environ.get("ELASTIC_CONVO_INDEX_NAME"))

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
                    es_client.index(index=os.environ.get("ELASTIC_CONVO_INDEX_NAME"), body=json.dumps(conversation_data))
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

def get_elasticsearch_results(es_client, query, selected_indices, size):
    retrievers = []
    indices = []

    for index in selected_indices:
        retrievers.append({
            "standard": {
                "query": {
                    "nested": {
                        "path": "body.inference.chunks",
                        "query": {
                            "sparse_vector": {
                                "inference_id": os.environ.get("ELASTIC_MODEL_ID"),
                                "field": "body.inference.chunks.embeddings",
                                "query": query
                            }
                        },
                        "inner_hits": {
                            "size": 2,
                            "name": f"{index}.body",
                            "_source": [
                                "body.inference.chunks.text"
                            ]
                        }
                    }
                }
            }
        })
        indices.append(index)

    if len(retrievers) >= 2:
        es_query = {
            "retriever": {
                "rrf": {
                    "retrievers": retrievers
                }
            },
            "size": size
        }
    elif len(retrievers) == 1:
        es_query = {
            "retriever": retrievers[0],
            "size": size
        }
    else:
        return []

    if not indices:
        return []  # Return empty list if no indices are selected

    result = es_client.search(index=",".join(indices), body=es_query)
    return result["hits"]["hits"]

def create_RAG_context(results, query):
    context = ""
    for hit in results:
        index = hit['_index']
        filename = hit['_source'].get('filename', 'Unknown')
        context += f"\nContext Filename: {filename}\n"
        
        inner_hit_path = f"{index}.body"

        context_arr=[]

        if 'inner_hits' in hit and inner_hit_path in hit['inner_hits']:
            context_arr.append('\n --- \n'.join(inner_hit['_source']['text'] for inner_hit in hit['inner_hits'][inner_hit_path]['hits']['hits']))
        else:
            context_arr.append(json.dumps(hit['_source'], indent=2))
        
        context="".join(context_arr)+"\n"

    prompt = f"""
    Instructions:
    
    - You are an assistant for question-answering tasks.
    - Answer questions truthfully and factually using only the context presented.
    - If you don't know the answer, just say that you don't know, don't make up an answer.
    - Use markdown format for code examples.
    - You are correct, factual, precise, and reliable.
    
    Context:
    {context}

    Query:
    {query}
    
    """
    return prompt

def get_valid_indices(es_client, valid_index_list):
    valid_indices = []
    for index in valid_index_list:
        if es_client.indices.exists(index=index):
            count = es_client.count(index=index)['count']
            if count > 0:
                valid_indices.append(index)
    return valid_indices