from pathlib import Path
import uuid
import os

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from data_loader import load_and_chunk_pdf, embed_texts
from vector_db import QdrantStorage

load_dotenv()

st.set_page_config(page_title="RAG – PDF Q&A", page_icon="📄", layout="centered")


# ── helpers ──────────────────────────────────────────────────────────────────

def save_uploaded_pdf(file) -> Path:
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    file_path = uploads_dir / file.name
    file_path.write_bytes(file.getbuffer())
    return file_path


def ingest_pdf(pdf_path: Path, source_id: str) -> int:
    """Chunk → embed → upsert into Qdrant in batches to avoid OOM."""
    chunks = load_and_chunk_pdf(str(pdf_path))
    if not chunks:
        return 0
        
    storage = QdrantStorage()
    batch_size = 100
    
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i : i + batch_size]
        vecs = embed_texts(batch_chunks)
        
        # Calculate global indices for UUID generation
        ids = [
            str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source_id}:{i + j}"))
            for j in range(len(batch_chunks))
        ]
        payloads = [
            {"source": source_id, "text": batch_chunks[j]}
            for j in range(len(batch_chunks))
        ]
        
        storage.upsert(ids, vecs, payloads)
        
    return len(chunks)


def query_pdf(question: str, top_k: int = 5) -> dict:
    """Embed question → semantic search → Groq LLM → answer."""
    query_vec = embed_texts([question])[0]
    found = QdrantStorage().search(query_vec, top_k)

    context_block = "\n\n".join(f"- {c}" for c in found["contexts"])
    user_content = (
        "Use the following context to answer the question.\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {question}\n"
        "Answer concisely using the context above."
    )

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets.get("GROQ_API_KEY")
        except FileNotFoundError:
            pass
            
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing! Please set it in Streamlit Cloud Secrets or your .env file.")
        
    client = Groq(api_key=api_key)
    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You answer questions using only the provided context."},
            {"role": "user", "content": user_content},
        ],
        max_tokens=1024,
        temperature=0.2,
    )
    answer = res.choices[0].message.content.strip()
    return {"answer": answer, "sources": found["sources"], "num_contexts": len(found["contexts"])}


# ── UI ────────────────────────────────────────────────────────────────────────

st.title("📄 Upload a PDF to Ingest")
uploaded = st.file_uploader("Choose a PDF", type=["pdf"], accept_multiple_files=False)

if uploaded is not None:
    with st.spinner("Processing and ingesting PDF…"):
        path = save_uploaded_pdf(uploaded)
        try:
            count = ingest_pdf(path, source_id=uploaded.name)
            st.success(f"✅ Ingested **{uploaded.name}** — {count} chunks stored.")
        except Exception as e:
            st.error(f"❌ Ingestion failed: {e}")
    st.caption("You can upload another PDF if you like.")

st.divider()
st.title("💬 Ask a question about your PDFs")

with st.form("rag_query_form"):
    question = st.text_input("Your question")
    top_k = st.number_input("Chunks to retrieve", min_value=1, max_value=20, value=5, step=1)
    submitted = st.form_submit_button("Ask")

    if submitted and question.strip():
        with st.spinner("Searching and generating answer…"):
            try:
                result = query_pdf(question.strip(), int(top_k))
                st.subheader("Answer")
                st.write(result["answer"] or "(No answer)")
                if result["sources"]:
                    st.caption("Sources")
                    for s in result["sources"]:
                        st.write(f"- {s}")
            except Exception as e:
                st.error(f"❌ Query failed: {e}")
