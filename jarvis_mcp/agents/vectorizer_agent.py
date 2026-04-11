"""Vectorizer Agent - converts documents to embeddings and stores in knowledge base."""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import json


class VectorizerAgent:
    """Converts documents to vector embeddings for knowledge base."""

    def __init__(self, knowledge_base):
        """Initialize vectorizer with knowledge base reference."""
        self.kb = knowledge_base

    async def vectorize_document(self, file_path: str) -> Optional[str]:
        """Extract text from document and create embeddings."""
        path = Path(file_path)

        if not path.exists():
            return None

        # Extract content based on file type
        content = await self._extract_content(path)
        if not content:
            return None

        # Ingest to knowledge base
        doc_id = await self.kb.ingest_document(
            doc_path=str(path),
            doc_type=path.suffix.lower(),
            content=content,
            metadata={
                "filename": path.name,
                "size_kb": path.stat().st_size / 1024
            }
        )

        return doc_id

    async def _extract_content(self, file_path: Path) -> Optional[str]:
        """Extract text content from document."""
        extension = file_path.suffix.lower()

        if extension == ".txt":
            return self._extract_text(file_path)
        elif extension == ".json":
            return self._extract_json(file_path)
        elif extension in [".pdf", ".docx", ".xlsx", ".pptx"]:
            return self._extract_metadata(file_path)
        else:
            return None

    def _extract_text(self, file_path: Path) -> str:
        """Extract from text file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def _extract_json(self, file_path: Path) -> str:
        """Extract from JSON file."""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                return json.dumps(data, indent=2)
        except Exception:
            return ""

    def _extract_metadata(self, file_path: Path) -> str:
        """Extract metadata from binary files."""
        stat = file_path.stat()
        return f"Document: {file_path.name}, Type: {file_path.suffix}, Size: {stat.st_size} bytes"

    async def vectorize_batch(self, file_paths: list) -> Dict[str, str]:
        """Vectorize multiple documents in parallel."""
        results = {}

        for file_path in file_paths:
            try:
                doc_id = await self.vectorize_document(file_path)
                if doc_id:
                    results[file_path] = doc_id
            except Exception as e:
                results[file_path] = f"Error: {str(e)}"

        return results

    async def get_vectorizer_status(self) -> Dict[str, Any]:
        """Get current vectorizer status."""
        kb_summary = await self.kb.get_account_summary()

        return {
            "knowledge_base_status": kb_summary,
            "vectorizer_ready": True,
            "embedding_dimension": 100
        }
