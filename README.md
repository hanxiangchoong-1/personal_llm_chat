# LLM ChatApp 

## Prerequisites 

1. An Elastic Cloud Deployment 
    * If you want to use RAG mode: 
        * An inference API for a trained model 
        * At least one index set-up for RAG, preferably using [Elastic 8.15 and semantic_text](https://www.linkedin.com/pulse/search-elastic-815-building-rag-extremely-quickly-without-choong-p0pvc/?trackingId=OAZFvBapTmuC22IjIoIoJQ%3D%3D)
2. An Azure OpenAI Deployment (Other LLMs and cloud providers are possible but require a bit of editing at the moment)
3. A Python Installation (This project was done using 3.12)

## Set-Up 

Clone the repo, navigate to main folder, and install dependencies.
```bash
pip install -r requirements.txt
```

Create a .env file and fill out the following:

```
ELASTIC_ENDPOINT="<YOUR ELASTIC CLOUD ENDPOINT>"
ELASTIC_API_KEY="<YOUR ELASTIC CLOUD API KEY>"
ELASTIC_CONVO_INDEX_NAME="<YOUR ELASTIC CLOUD API KEY>"
ELASTIC_MODEL_ID="elser_v2"

AZURE_OPENAI_KEY_1=""
AZURE_OPENAI_KEY_2=""
AZURE_OPENAI_REGION=""
AZURE_OPENAI_ENDPOINT=""
```