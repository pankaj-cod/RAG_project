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
    for t in texts:
        chunks.extend(splitter.split_text(t))
    return chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = _get_embed_model()
    # fastembed returns a generator of numpy arrays
    return [vec.tolist() for vec in model.embed(texts)]
