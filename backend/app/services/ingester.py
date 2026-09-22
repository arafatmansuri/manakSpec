import json
import asyncpg
from typing import Optional, Dict, Any
from app.services.parser import document_parser
from app.services.extractor import bis_extractor
from app.services.embedder import gemini_embedder

class BISIngestionService:
    async def ingest_document(
        self,
        conn: asyncpg.Connection,
        file_bytes: Optional[bytes] = None,
        filename: str = "",
        json_payload: Optional[Dict[str, Any]] = None,
        relation_type: Optional[str] = None,
        parent_is_number: Optional[str] = None,
        manual_overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Unified Ingestion Pipeline:
        - Handles both PDF and JSON files.
        - Validates extraction quality.
        - Distinguishes Base Standards from Amendments.
        - Populates relational metadata and dynamic JSONB technical specifications.
        """
        manual_overrides = manual_overrides or {}
        raw_text = ""
        tech_specs: Dict[str, Any] = {}

        # 1. FILE INSPECTION & PARSING (JSON vs PDF)
        if filename.lower().endswith(".json") or json_payload:
            payload = json_payload or json.loads(file_bytes.decode("utf-8"))
            is_number = payload.get("is_number") or manual_overrides.get("is_number")
            title = payload.get("title") or manual_overrides.get("title")
            publication_year = payload.get("publication_year") or manual_overrides.get("publication_year")
            scope_text = payload.get("scope_text") or manual_overrides.get("scope_text", "")
            is_mandatory_qco = payload.get("is_mandatory_qco", False)
            scheme_type = payload.get("scheme_type", "Scheme-I")
            committee_code = payload.get("committee_code")
            gazette_notice_id = payload.get("gazette_notice_id")
            reaffirmation_year = payload.get("reaffirmation_year")
            tech_specs = payload.get("technical_specifications", {})
            relations_data = payload.get("relations", [])
        else:
            # Handle PDF Ingestion
            if filename.lower().endswith(".pdf") or not filename:
                raw_text = document_parser.extract_text_from_pdf(file_bytes)
            else:
                raw_text = document_parser.extract_text_from_image(file_bytes)

            # Quality Check
            is_valid, failure_reason = bis_extractor.validate_text_quality(raw_text)
            if not is_valid:
                raise ValueError(f"Quality Check Failed: {failure_reason}")

            # Extract Metadata
            is_number = manual_overrides.get("is_number") or bis_extractor.extract_is_number(raw_text) or "IS UNKNOWN"
            publication_year = manual_overrides.get("publication_year") or bis_extractor.extract_publication_year(raw_text, is_number)
            title = manual_overrides.get("title") or f"Indian Standard {is_number}"
            scope_text = manual_overrides.get("scope_text") or bis_extractor.extract_scope(raw_text)
            is_mandatory_qco = manual_overrides.get("is_mandatory_qco", False)
            scheme_type = manual_overrides.get("scheme_type", "Scheme-I")
            
            auto_committee, auto_gazette = bis_extractor.extract_committee_and_gazette(raw_text)
            committee_code = manual_overrides.get("committee_code") or auto_committee
            gazette_notice_id = manual_overrides.get("gazette_notice_id") or auto_gazette
            reaffirmation_year = manual_overrides.get("reaffirmation_year")
            
            tech_specs = manual_overrides.get("technical_specifications", {})
            relations_data = bis_extractor.extract_annex_a_references(raw_text)

        # 2. EMBEDDING GENERATION
        embedding = await gemini_embedder.pipeline_gemini_embedder(scope_text)
        vector_str = "[" + ",".join(map(str, embedding)) + "]"

        # 3. ROUTING BY RELATION TYPE (Amendment vs Base Standard)
        explicit_relation = relation_type or manual_overrides.get("relation_type")

        if explicit_relation == "Amendment" or parent_is_number:
            target_parent = parent_is_number or is_number
            
            # Insert record into standard_relations instead of overwriting base standard
            await conn.execute(
                """
                INSERT INTO standard_relations (parent_is_number, relation_type, related_is_number, title_or_description)
                VALUES ($1, $2, $3, $4);
                """,
                target_parent, "Amendment", is_number, title
            )
            
            # Update latest amendment info on parent standard
            await conn.execute(
                """
                UPDATE indian_standards 
                SET latest_amendment = $1, amendment_details = $2, updated_at = CURRENT_TIMESTAMP
                WHERE is_number = $3;
                """,
                is_number, title, target_parent
            )

            return {
                "status": "success",
                "type": "Amendment Linked",
                "parent_is_number": target_parent,
                "amendment_is_number": is_number
            }

        # 4. BASE STANDARD UPSERT (Primary Table)
        upsert_sql = """
            INSERT INTO indian_standards (
                is_number, title, publication_year, status, scope_text, 
                is_mandatory_qco, scheme_type, committee_code, gazette_notice_id,
                reaffirmation_year, technical_specifications, scope_embedding
            ) VALUES ($1, $2, $3, 'Active', $4, $5, $6, $7, $8, $9, $10::jsonb, $11::vector)
            ON CONFLICT (is_number) DO UPDATE SET
                title = EXCLUDED.title,
                publication_year = EXCLUDED.publication_year,
                scope_text = EXCLUDED.scope_text,
                is_mandatory_qco = EXCLUDED.is_mandatory_qco,
                scheme_type = EXCLUDED.scheme_type,
                committee_code = COALESCE(EXCLUDED.committee_code, indian_standards.committee_code),
                gazette_notice_id = COALESCE(EXCLUDED.gazette_notice_id, indian_standards.gazette_notice_id),
                reaffirmation_year = COALESCE(EXCLUDED.reaffirmation_year, indian_standards.reaffirmation_year),
                technical_specifications = indian_standards.technical_specifications || EXCLUDED.technical_specifications,
                scope_embedding = EXCLUDED.scope_embedding,
                updated_at = CURRENT_TIMESTAMP;
        """
        
        await conn.execute(
            upsert_sql,
            is_number, title, publication_year, scope_text,
            is_mandatory_qco, scheme_type, committee_code, gazette_notice_id,
            reaffirmation_year, json.dumps(tech_specs), vector_str
        )

        # 5. TARGETED RELATIONS UPDATE (Prevents Relational Overwrites)
        if relations_data:
            # Delete ONLY Normative References for this parent (preserves Amendments, Safety Codes, etc.)
            await conn.execute(
                """
                DELETE FROM standard_relations 
                WHERE parent_is_number = $1 AND relation_type = 'Normative Reference';
                """, 
                is_number
            )

            relation_records = [
                (
                    is_number, 
                    ref.get("relation_type", "Normative Reference"), 
                    ref.get("related_is_number"), 
                    ref.get("title_or_description", "")
                )
                for ref in relations_data
            ]
            
            await conn.executemany(
                """
                INSERT INTO standard_relations (parent_is_number, relation_type, related_is_number, title_or_description)
                VALUES ($1, $2, $3, $4);
                """,
                relation_records
            )

        return {
            "status": "success",
            "type": "Base Standard Upserted",
            "is_number": is_number,
            "title": title,
            "publication_year": publication_year,
            "committee_code": committee_code,
            "relations_added": len(relations_data)
        }

bis_ingester = BISIngestionService()