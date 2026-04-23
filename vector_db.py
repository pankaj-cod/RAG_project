import os
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct


class QdrantStorage:
    def __init__(self, collection: str = "docs", dim: int = 768):
        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        api_key = os.getenv("QDRANT_API_KEY")  # None for local, required for Qdrant Cloud

        self.client = QdrantClient(url=url, api_key=api_key, timeout=30)
        self.collection = collection

        # Create collection only if it doesn't already exist
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=dim,
                    distance=Distance.COSINE,
                ),
            )

    def upsert(self, ids: list, vectors: list, payloads: list) -> None:
        points = [
            PointStruct(id=ids[i], vector=vectors[i], payload=payloads[i])
            for i in range(len(ids))
        ]
        self.client.upsert(collection_name=self.collection, points=points)

    def search(self, query_vector: list[float], top_k: int = 5) -> dict:
        results = self.client.query_points(
            collection_name=self.collection,
            query=query_vector,
            with_payload=True,
            limit=top_k,
        ).points

        contexts: list[str] = []
        sources: set[str] = set()

        for r in results:
            payload = r.payload or {}
            text = payload.get("text", "")
            source = payload.get("source", "")
            if text:
                contexts.append(text)
                sources.add(source)

        return {"contexts": contexts, "sources": list(sources)}