from app.core.db import get_db_connection
from app.services.embedder import embedder
from typing import Dict, Any

def search_relevant_standards(query_text: str, top_k: int = 3) -> Dict[str, Any]:
    """
    1. Embeds query text locally
    2. Runs HNSW Cosine Similarity search on scope_embedding
    3. Fetches related normative standards via SQL JOINs
    """
    query_vector = embedder.generate_embedding(query_text)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Vector Similarity Search
    search_query = """
        SELECT is_number, title, publication_year, scope_text, is_mandatory_qco,
               (1 - (scope_embedding <=> %s::vector)) AS similarity
        FROM indian_standards
        ORDER BY scope_embedding <=> %s::vector
        LIMIT %s;
    """
    cursor.execute(search_query, (query_vector, query_vector, top_k))
    columns = [col[0] for col in cursor.description]
    top_matches = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    if not top_matches:
        cursor.close()
        conn.close()
        return {"primary_standards": [], "allied_references": []}
    
    primary_is_numbers = [item["is_number"] for item in top_matches]
    
    # 2. Array/Relation Lookup for Annex A Normative References
    relation_query = """
        SELECT parent_is_number, relation_type, related_is_number, title_or_description
        FROM standard_relations
        WHERE parent_is_number = ANY(%s);
    """
    cursor.execute(relation_query, (primary_is_numbers,))
    rel_columns = [col[0] for col in cursor.description]
    relations = [dict(zip(rel_columns, row)) for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return {
        "primary_standards": top_matches,
        "allied_references": relations
    }