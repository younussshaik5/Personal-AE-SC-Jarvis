from typing import Dict, Any, Optional, List

class ContextAggregatorAgent:
    """Aggregates knowledge from knowledge base and provides enriched context."""

    def __init__(self, knowledge_base):
        self.kb = knowledge_base

    async def enrich_skill_context(self, skill_name: str, base_prompt: str, query: Optional[str] = None) -> str:
        search_query = query or skill_name
        relevant_docs = await self.kb.retrieve_relevant(search_query, top_k=3)

        if not relevant_docs:
            return base_prompt

        context_section = self._build_context_section(relevant_docs)
        enriched_prompt = f"{context_section}\n\n{base_prompt}"
        return enriched_prompt

    def _build_context_section(self, documents: List[Dict[str, Any]]) -> str:
        if not documents:
            return ""

        section = "## LEARNED CONTEXT\n\n"
        for result in documents:
            doc = result["document"]
            similarity = result["similarity"]
            section += f"### {doc['path']} (Relevance: {similarity:.2f})\n"
            section += f"Content: {doc['content'][:100]}...\n\n"

        return section

    async def get_account_context(self) -> Dict[str, Any]:
        kb_summary = await self.kb.get_account_summary()
        return {
            "knowledge_available": kb_summary["total_documents"] > 0,
            "document_count": kb_summary["total_documents"],
            "context_enrichment_enabled": True
        }

    async def get_aggregator_status(self) -> Dict[str, Any]:
        account_context = await self.get_account_context()
        return {"aggregator_ready": True, "context_enrichment_active": True, **account_context}
