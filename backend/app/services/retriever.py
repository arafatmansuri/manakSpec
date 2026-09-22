import json
import asyncpg
from app.services.embedder import gemini_embedder
from typing import List, Dict, Any

class StandardRetrieverService:
    async def search_standards(self, conn: asyncpg.Connection, query_text: str, top_k: int = 5) -> Dict[str, Any]:
        # 1. Generate vector embedding
        embedding_vector = gemini_embedder.generate_embedding(query_text)
        vector_str = "[" + ",".join(map(str, embedding_vector)) + "]"

        # 2. Vector search matching indian_standards schema
        search_sql = """
            SELECT 
                is_number, 
                title, 
                publication_year, 
                status, 
                latest_amendment, 
                amendment_details, 
                scope_text, 
                COALESCE(is_mandatory_qco, false) AS is_mandatory_qco, 
                scheme_type,
                committee_code,
                gazette_notice_id,
                reaffirmation_year,
                technical_specifications,
                (1 - (scope_embedding <=> $1::vector)) AS similarity_score
            FROM indian_standards
            ORDER BY scope_embedding <=> $1::vector
            LIMIT $2;
        """
        rows = await conn.fetch(search_sql, vector_str, top_k)
        
        primary_standards = []
        for row in rows:
            data = dict(row)
            # Parse stringified jsonb if asyncpg returns standard string representation
            if isinstance(data.get("technical_specifications"), str):
                try:
                    data["technical_specifications"] = json.loads(data["technical_specifications"])
                except Exception:
                    data["technical_specifications"] = {}
            primary_standards.append(data)

        parent_ids = [item["is_number"] for item in primary_standards]

        # 3. Allied references fetch matching standard_relations
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