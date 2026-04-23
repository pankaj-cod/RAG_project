<<<<<<< HEAD
from pathlib import Path
from llama_index.readers.file import PDFReader
from llama_index.core.node_parser import SentenceSplitter
from dotenv import load_dotenv

load_dotenv()

# fastembed runs fully in-process — no Ollama server needed.
# nomic-embed-text-v1.5 produces 768-dim vectors, matching the Qdrant collection.
from fastembed import TextEmbedding

EMBED_DIM = 768
_embed_model: TextEmbedding | None = None


def _get_embed_model() -> TextEmbedding:
    """Lazy-load the embedding model once per process."""
    global _embed_model
    if _embed_model is None:
        _embed_model = TextEmbedding("nomic-ai/nomic-embed-text-v1.5")
    return _embed_model


splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=200)


def load_and_chunk_pdf(path: str) -> list[str]:
    docs = PDFReader().load_data(file=path)
    texts = [d.text for d in docs if getattr(d, "text", None)]
    chunks: list[str] = []
=======
from groq import Groq
from llama_index.readers.file import PDFReader
from llama_index.core.node_parser import SentenceSplitter
from dotenv import load_dotenv
import requests

load_dotenv()

client = Groq()

# Use local Ollama embeddings instead of OpenAI/Groq
EMBED_MODEL = "nomic-embed-text"
EMBED_DIM = 768

splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=200)

def load_and_chunk_pdf(path: str):
    docs = PDFReader().load_data(file=path)
    texts = [d.text for d in docs if getattr(d, "text", None)]
    chunks = []
>>>>>>> 790b281 (Finalisation of RAG project)
    for t in texts:
        chunks.extend(splitter.split_text(t))
    return chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
<<<<<<< HEAD
    model = _get_embed_model()
    # fastembed returns a generator of numpy arrays
    return [vec.tolist() for vec in model.embed(texts)]
=======
    embeddings = []

    for text in texts:
        res = requests.post(
            "http://localhost:11434/api/embeddings",
            json={
                "model": EMBED_MODEL,
                "prompt": text
            }
        )
        embeddings.append(res.json()["embedding"])

    return embeddings

>>>>>>> 790b281 (Finalisation of RAG project)
