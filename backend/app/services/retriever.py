import json
import re
import asyncpg
from app.services.embedder import gemini_embedder
from app.services.extractor import bis_extractor
from typing import List, Dict, Any, Optional

class StandardRetrieverService:
    def _extract_is_code(self, query: str) -> Optional[str]:
        """Finds any explicit Indian Standard code pattern like 'IS 16106' or 'IS 456'."""
        match = re.search(r'\bIS\s*(\d{2,6})\b', query, re.IGNORECASE)
        if match:
            return f"IS {match.group(1)}"
        return None

    def _extract_key_terms(self, query: str) -> str:
        """Extracts significant keywords for text search."""
        words = re.findall(r'\b[A-Za-z]{3,}\b', query)
        filtered = [w for w in words if w.lower() not in {"standard", "specification", "procurement", "tender", "indian", "need", "find", "applicable"}]
        return " ".join(filtered[:4])

    async def search_standards(self, conn: asyncpg.Connection, query_text: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Executes a hybrid search combining:
        1. Dense semantic vector similarity (Cosine similarity via pgvector HNSW index)
        2. Lexical exact code matching for IS numbers (e.g. IS 10322, IS 694)
        3. Title keyword matching
        """
        # 1. Generate vector embedding
        embedding_vector = gemini_embedder.generate_embedding(query_text)
        vector_str = "[" + ",".join(map(str, embedding_vector)) + "]"

        # 2. Extract lexical cues
        explicit_is_code = self._extract_is_code(query_text) or ""
        key_terms = self._extract_key_terms(query_text)

        # 3. Hybrid search SQL with weighted fusion
        search_sql = """
            WITH scored_standards AS (
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
                    COALESCE((1 - (scope_embedding <=> $1::vector)), 0.0) AS semantic_score,
                    (
                        CASE 
                            WHEN $3 != '' AND is_number ILIKE '%' || $3 || '%' THEN 1.0
                            WHEN $3 != '' AND title ILIKE '%' || $3 || '%' THEN 0.6
                            ELSE 0.0
                        END
                    ) AS is_code_match_bonus,
                    (
                        CASE 
                            WHEN $4 != '' AND title ILIKE '%' || $4 || '%' THEN 0.3
                            ELSE 0.0
                        END
                    ) AS title_keyword_bonus
                FROM indian_standards
            )
            SELECT 
                is_number, 
                title, 
                publication_year, 
                status, 
                latest_amendment, 
                amendment_details, 
                scope_text, 
                is_mandatory_qco, 
                scheme_type,
                committee_code,
                gazette_notice_id,
                reaffirmation_year,
                technical_specifications,
                LEAST(1.0, GREATEST(0.0, 
                    (0.65 * semantic_score) + is_code_match_bonus + title_keyword_bonus
                )) AS similarity_score
            FROM scored_standards
            ORDER BY 
                is_code_match_bonus DESC,
                ((0.65 * semantic_score) + is_code_match_bonus + title_keyword_bonus) DESC
            LIMIT $2;
        """
        rows = await conn.fetch(search_sql, vector_str, top_k, explicit_is_code, key_terms)
        
        primary_standards = []
        for row in rows:
            data = dict(row)
            # Parse stringified jsonb if needed
            if isinstance(data.get("technical_specifications"), str):
                try:
                    data["technical_specifications"] = json.loads(data["technical_specifications"])
                except Exception:
                    data["technical_specifications"] = {}
            primary_standards.append(data)

        parent_ids = [item["is_number"] for item in primary_standards]

        # 4. Allied references fetch matching standard_relations with dynamic classification
        relations_sql = """
            SELECT parent_is_number, relation_type, related_is_number, title_or_description
            FROM standard_relations
            WHERE parent_is_number = ANY($1::varchar[]);
        """
        rel_rows = await conn.fetch(relations_sql, parent_ids) if parent_ids else []
        allied_references = []
        for row in rel_rows:
            rel_dict = dict(row)
            # If relation_type is generic 'Normative Reference', classify using title/description
            if rel_dict.get("relation_type") == "Normative Reference":
                rel_dict["relation_type"] = bis_extractor.classify_relation_type(
                    rel_dict.get("title_or_description", "")
                )
            allied_references.append(rel_dict)

        return {
            "primary_standards": primary_standards,
            "allied_references": allied_references
        }

retriever_service = StandardRetrieverService()