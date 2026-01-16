# Multivitamin Recommendation Chatbot

A RAG-based chatbot that provides personalized multivitamin recommendations based on cognitive impairment test results.

## Features

- **Local RAG System**: Uses FAISS for local vector storage
- **Cognitive Analysis**: Analyzes gamified cognitive test results  
- **Personalized Recommendations**: Provides tailored multivitamin suggestions
- **Local Processing**: All data stays on your machine
- **Interactive Interface**: Streamlit-based chat interface

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run app.py
```

## Project Structure

```
├── app.py                          # Main Streamlit application
├── src/
│   ├── __init__.py
│   ├── vector_store.py             # FAISS vector database management
│   ├── rag_system.py               # RAG implementation
│   ├── cognitive_analyzer.py       # Test result analysis
│   ├── chatbot.py                  # Chatbot logic
│   └── data_loader.py              # Knowledge base loader
├── data/
│   ├── multivitamin_knowledge.json # Multivitamin database
│   └── cognitive_mapping.json      # Cognitive-vitamin mappings
├── knowledge_base/                 # Vector embeddings storage
└── requirements.txt
```

## Usage

1. Upload your cognitive test results
2. Chat with the bot about your symptoms
3. Receive personalized multivitamin recommendations
4. Get detailed information about recommended supplements

## Example Test Results Format

```json
{
    "test_type": "gamified_cognitive",
    "scores": {
        "memory": 75,
        "attention": 60,
        "processing_speed": 80,
        "executive_function": 70
    },
    "impairments": ["mild_memory_loss", "attention_deficit"],
    "age": 45,
    "gender": "female"
}
```