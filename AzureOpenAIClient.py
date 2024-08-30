import os
from openai import AzureOpenAI
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

class AzureOpenAIClient:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_KEY_1"),
            api_version="2024-06-01",
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT")
        )

    def generate_streaming_response(self, prompt, model="gpt-4o", system_prompt=""):
        response_text = ""
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            for chunk in self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                stream=True,
                max_tokens=4096
            ):
                if len(chunk.choices) > 0:
                    if chunk.choices[0].delta.content is not None:
                        response_text += chunk.choices[0].delta.content
                        message_placeholder.markdown(response_text + "▌")
        return response_text