import asyncpg
from app.services.embedder import gemini_embedder
from typing import List, Dict, Any

class StandardRetrieverService:
    async def search_standards(self, conn: asyncpg.Connection, query_text: str, top_k: int = 3) -> Dict[str, Any]:
        # 1. Generate vector embedding
        embedding_vector = gemini_embedder.generate_embedding(query_text)
        vector_str = "[" + ",".join(map(str, embedding_vector)) + "]"

        # 2. Direct SQL Query with pgvector <=> cosine operator
        search_sql = """
            SELECT is_number, title, publication_year, status, scope_text, is_mandatory_qco, scheme_type,
                   (1 - (scope_embedding <=> $1::vector)) AS similarity_score
            FROM indian_standards
            ORDER BY scope_embedding <=> $1::vector
            LIMIT $2;
        """
        rows = await conn.fetch(search_sql, vector_str, top_k)
        primary_standards = [dict(row) for row in rows]

        if not primary_standards:
            return {"primary_standards": [], "allied_references": []}

        parent_ids = [item["is_number"] for item in primary_standards]

        # 3. SQL Array JOIN for Normative References
        relations_sql = """
            SELECT parent_is_number, relation_type, related_is_number, title_or_description
            FROM standard_relations
            WHERE parent_is_number = ANY($1::varchar[]);
        """
        rel_rows = await conn.fetch(relations_sql, parent_ids)
        allied_references = [dict(row) for row in rel_rows]

        return {
            "primary_standards": primary_standards,
            "allied_references": allied_references
        }

retriever_service = StandardRetrieverService()