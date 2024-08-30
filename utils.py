from datetime import datetime

def get_current_time():
    return datetime.now().strftime("%H:%M")

def count_words_in_conversation(messages, conversation_length):
    word_count = 0
    for message in messages[-conversation_length:]:
        word_count += len(message["content"].split())+1
    return word_count

def create_conversational_prompt(history, conversation_length=10):
    conversational_prompt="" 
    for segment in history[-conversation_length:]:
        conversational_prompt+=f'''
{segment["role"]}:
{segment["content"]}
''' 
    return conversational_prompt