from datetime import datetime
from datetime import timezone

def get_current_time():
    return datetime.now(timezone.utc).isoformat()

def count_words_in_conversation(messages, conversation_length):
    word_count = 0
    for message in messages[-conversation_length:]:
        word_count += len(message["content"].split())+1
        if message["RAG_context"] != "":
            word_count += len(message["RAG_context"].split())
    return word_count

def create_conversational_prompt(history, conversation_length=10):
    conversational_prompt="" 
    for segment in history[-conversation_length:]:
        if segment["RAG_context"] != "":
            conversational_prompt+=f'''
{segment["role"]}:
{segment["RAG_context"]}
''' 
        else:
            conversational_prompt+=f'''
{segment["role"]}:
{segment["content"]}
''' 
    return conversational_prompt