import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

log = logging.getLogger(__name__)

_EMBED_MODEL  = "nvidia/nv-embedqa-e5-v5"
_EMBED_BASE   = "https://integrate.api.nvidia.com/v1"
_EMBED_DIM    = 1024   # NV-Embed output dimension
_FALLBACK_DIM = 100    # TF-vector fallback dimension


class KnowledgeBase:
    """
    Manages vector storage, embeddings, and knowledge retrieval.

    Embeddings: NVIDIA NV-Embed-QA-E5-v5 (1024-dim semantic vectors) via the
    same NVIDIA key pool used by LLMManager.  Falls back to term-frequency
    vectors when the API key is missing or the call fails.
    """

    def __init__(self, account_path: str):
        self.account_path = Path(account_path)
        self.kb_dir = self.account_path / ".knowledge_base"
        self.kb_dir.mkdir(exist_ok=True)

        self.documents_file = self.kb_dir / "documents.json"
        self.vectors_file = self.kb_dir / "vectors.json"
        self.metadata_file = self.kb_dir / "metadata.json"

        self._initialize_storage()

    def _initialize_storage(self):
        for file_path in [self.documents_file, self.vectors_file, self.metadata_file]:
            if not file_path.exists():
                with open(file_path, "w") as f:
                    json.dump({}, f, indent=2)

    async def ingest_document(self, doc_path: str, doc_type: str, content: str, metadata: Dict[str, Any] = None) -> str:
        import hashlib
        doc_id = hashlib.md5(f"{doc_path}{datetime.now()}".encode()).hexdigest()[:12]

        docs = self._load_json(self.documents_file)
        docs[doc_id] = {
            "path": doc_path,
            "type": doc_type,
            "content": content[:5000],
            "ingested_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self._save_json(self.documents_file, docs)

        embedding = self._create_embedding(content)
        vectors = self._load_json(self.vectors_file)
        vectors[doc_id] = embedding
        self._save_json(self.vectors_file, vectors)

        meta = self._load_json(self.metadata_file)
        meta["last_ingestion"] = datetime.now().isoformat()
        meta["total_documents"] = len(docs)
        self._save_json(self.metadata_file, meta)

        return doc_id

    def _create_embedding(self, text: str) -> List[float]:
        """
        NVIDIA NV-Embed semantic embedding (1024-dim).
        Falls back to term-frequency vector if API key is absent or call fails.
        """
        api_key = os.getenv("NVIDIA_API_KEY", "")
        if not api_key:
            return self._create_embedding_fallback(text)
        try:
            from openai import OpenAI
            client = OpenAI(base_url=_EMBED_BASE, api_key=api_key)
            response = client.embeddings.create(
                input=[text[:2048]],   # NV-Embed token limit
                model=_EMBED_MODEL,
                encoding_format="float",
            )
            embedding = response.data[0].embedding
            log.debug(f"Semantic embedding: {len(embedding)}-dim for {len(text)} chars")
            return embedding
        except Exception as e:
            log.warning(f"Embedding API failed ({e}) — using TF fallback")
            return self._create_embedding_fallback(text)

    def _create_embedding_fallback(self, text: str) -> List[float]:
        """100-dim term-frequency vector — used when NVIDIA embed API is unavailable."""
        words = text.lower().split()
        word_freq: Dict[str, int] = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:_FALLBACK_DIM]
        max_freq = top_words[0][1] if top_words else 1

        embedding = [freq / max_freq for _, freq in top_words]
        while len(embedding) < _FALLBACK_DIM:
            embedding.append(0.0)
        return embedding[:_FALLBACK_DIM]

    async def retrieve_relevant(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self._create_embedding(query)
        docs = self._load_json(self.documents_file)
        vectors = self._load_json(self.vectors_file)

        similarities = []
        for doc_id, vector in vectors.items():
            if doc_id in docs:
                similarity = self._cosine_similarity(query_embedding, vector)
                similarities.append({"doc_id": doc_id, "similarity": similarity, "document": docs[doc_id]})

        top_results = sorted(similarities, key=lambda x: x["similarity"], reverse=True)[:top_k]
        return top_results

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = sum(a ** 2 for a in vec1) ** 0.5
        mag2 = sum(b ** 2 for b in vec2) ** 0.5

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    async def get_account_summary(self) -> Dict[str, Any]:
        meta = self._load_json(self.metadata_file)
        docs = self._load_json(self.documents_file)

        return {
            "total_documents": len(docs),
            "last_ingestion": meta.get("last_ingestion", "Never"),
            "knowledge_ready": len(docs) > 0
        }

    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_json(self, file_path: Path, data: Dict[str, Any]):
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
