# RAG - Retrieval-Augmented Generation Application

A production-ready RAG system that enables you to upload PDF documents, ingest them into a vector database, and ask questions to get AI-generated answers based on the document content.

## Features

- **PDF Ingestion**: Upload and process PDF documents automatically
- **Semantic Search**: Find relevant content using vector similarity
- **AI-Powered Answers**: Get contextual answers from your documents using LLMs
- **Event-Driven Architecture**: Built with Inngest for reliable workflow orchestration
- **Web UI**: Streamlit interface for easy interaction

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│  Streamlit  │────>│   Inngest    │────>│  FastAPI    │────>│   Qdrant    │
│     UI      │     │   Events     │     │   Server    │     │   Vector DB │
└─────────────┘     └──────────────┘     └─────────────┘     └─────────────┘
                                                       │
                                                       │
                                                ┌───────▼───────┐
                                                │    Ollama     │
                                                │  Embeddings   │
                                                └───────────────┘
                                                       │
                                                ┌───────▼───────┐
                                                │     Groq      │
                                                │     LLM       │
                                                └───────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Web Framework | FastAPI |
| UI | Streamlit |
| Workflow Orchestration | Inngest |
| Vector Database | Qdrant |
| Embeddings | Ollama (nomic-embed-text) |
| LLM | Groq (Llama 3.3 70B Versatile) |
| PDF Processing | LlamaIndex |
| Event Server | Uvicorn |

## Prerequisites

- Python 3.14+
- [Qdrant](https://qdrant.tech/documentation/quick-start/) running locally (default: `http://localhost:6333`)
- [Ollama](https://ollama.com/) running locally with `nomic-embed-text` model
- [Inngest Dev Server](https://www.inngest.com/docs/local) running (default: `http://127.0.0.1:8288`)
- Groq API key (get one at [groq.com](https://groq.com))

## Installation

1. **Clone the repository**:
   ```bash
   cd /Users/pankaj/Desktop/RAG
   ```

2. **Install dependencies**:
   ```bash
   pip install -e .
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   INNGEST_API_BASE=http://127.0.0.1:8288/v1
   ```

4. **Start required services**:

   **Qdrant** (if not running):
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

   **Ollama** (if not running):
   ```bash
   ollama serve
   ollama pull nomic-embed-text
   ```

   **Inngest Dev Server**:
   ```bash
   inngest dev
   ```

## Usage

### Start the Application

1. **Start the FastAPI server**:
   ```bash
   uvicorn main:app --reload
   ```

2. **Start the Streamlit UI** (in a separate terminal):
   ```bash
   streamlit run streamlit.py
   ```

3. **Access the UI**:
   Open http://localhost:8501 in your browser

### Workflow

1. **Upload a PDF**:
   - Use the file uploader to select a PDF document
   - Click to upload and trigger the ingestion process
   - The document will be processed, chunked, and stored in Qdrant

2. **Ask Questions**:
   - Enter your question in the text input
   - Adjust the number of context chunks to retrieve (default: 5)
   - Submit to get an AI-generated answer based on your documents

## Project Structure

```
RAG/
├── main.py              # FastAPI server with Inngest functions
├── streamlit.py         # Web UI for PDF upload and Q&A
├── data_loader.py       # PDF processing and embedding
├── vector_db.py        # Qdrant vector database wrapper
├── custom_types.py     # Pydantic models
├── pyproject.toml      # Project configuration
├── README.md           # This file
├── .env                # Environment variables (create this)
└── qdrant_storage/     # Local Qdrant data storage
```

## API Functions

### rag_ingest_pdf
Ingests a PDF document into the vector database.

**Event**: `rag/ingest_pdf`
**Data**:
- `pdf_path`: Path to the PDF file
- `source_id` (optional): Identifier for the document source

### rag_query_pdf_ai
Searches documents and generates an AI answer.

**Event**: `rag/query_pdf_ai`
**Data**:
- `question`: The question to answer
- `top_k` (optional): Number of context chunks to retrieve (default: 5)

**Response**:
- `answer`: AI-generated answer
- `sources`: List of source documents
- `num_contexts`: Number of context chunks used

## Configuration

### Embedding Model
- **Model**: `nomic-embed-text`
- **Dimensions**: 768
- **Endpoint**: `http://localhost:11434/api/embeddings`

### LLM Model
- **Provider**: Groq
- **Model**: `llama-3.3-70b-versatile`
- **Max Tokens**: 1024
- **Temperature**: 0.2

### Vector Database
- **Provider**: Qdrant
- **Collection**: `docs`
- **Distance Metric**: Cosine Similarity

## Dependencies

See `pyproject.toml` for the full list of dependencies:

- `fastapi>=0.128.8`
- `groq>=1.0.0`
- `inngest>=0.5.15`
- `llama-index-readers-file>=0.5.6`
- `python-dotenv>=1.2.1`
- `qdrant-client>=1.16.2`
- `streamlit>=1.54.0`
- `uvicorn>=0.40.0`

## Development

### Running Tests
```bash
# Run pytest
pytest
```

### Code Formatting
```bash
# Format code
ruff check . --fix
ruff format .
```

## License

MIT License - feel free to use this project for your own purposes.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

