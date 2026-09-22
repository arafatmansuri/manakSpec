import re
import json
from typing import Dict, Any, List, Optional, Tuple

class BISExtractorService:
    @staticmethod
    def extract_is_number(text: str) -> Optional[str]:
        """Extracts standard code like 'IS 19609:2026', 'IS 1180 (Part 1) : 2014', or 'IS 16106 : 2023'."""
        pattern = r"IS\s+\d+(?:\s*\([^)]+\))?(?:\s*:\s*\d{4})?"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(0).strip() if match else None

    @staticmethod
    def extract_publication_year(text: str, is_number: Optional[str] = None) -> int:
        """Extracts publication year from IS code or text context."""
        if is_number and ":" in is_number:
            year_match = re.search(r":\s*(\d{4})", is_number)
            if year_match:
                return int(year_match.group(1))
        
        year_match = re.search(r"\b(19\d{2}|20\d{2})\b", text)
        return int(year_match.group(1)) if year_match else 2026

    @staticmethod
    def extract_committee_and_gazette(text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extracts Committee Code (e.g. CED 11) and Gazette Notice ID if present in text."""
        committee_match = re.search(r"\b([A-Z]{2,4}\s+\d+)\b", text)
        gazette_match = re.search(r"\b(HQ-PUB\d+/\d+/\d{4}-PUB-BIS)\b", text, re.IGNORECASE)
        
        committee = committee_match.group(1).strip() if committee_match else None
        gazette = gazette_match.group(1).strip() if gazette_match else None
        return committee, gazette

    @staticmethod
    def validate_text_quality(text: str) -> Tuple[bool, str]:
        """
        Validates PDF text quality to prevent bad embeddings/corrupted data.
        Returns (is_valid, error_reason).
        """
        if len(text.strip()) < 200:
            return False, "Extracted text length is below 200 characters minimum threshold."
        
        required_anchors = ["BUREAU OF INDIAN STANDARDS", "INDIAN STANDARD", "IS", "SCOPE", "FOREWORD"]
        found_anchors = [anchor for anchor in required_anchors if anchor in text.upper()]
        
        if len(found_anchors) < 2:
            return False, f"Document failed anchor term check. Found anchors: {found_anchors}"
            
        return True, ""

    @staticmethod
    def extract_scope(text: str) -> str:
        """Extracts text under '1 SCOPE' or 'FOREWORD' sections."""
        scope_pattern = r"(?:1\s+SCOPE|SCOPE)([\s\S]*?)(?=\n\s*\d+\s+[A-Z]|FOREWORD|ANNEX|$)"
        match = re.search(scope_pattern, text, re.IGNORECASE)
        if match and len(match.group(1).strip()) > 30:
            return match.group(1).strip()[:2000]
        
        return text[:1000].strip()

    @staticmethod
    def extract_annex_a_references(text: str) -> List[Dict[str, str]]:
        """Parses referenced IS codes under 'ANNEX A' or 'NORMATIVE REFERENCES'."""
        annex_pattern = r"(?:ANNEX\s+A|NORMATIVE\s+REFERENCES)([\s\S]*?)(?=\n\s*ANNEX|\n\s*\d+\s+[A-Z]|$)"
        match = re.search(annex_pattern, text, re.IGNORECASE)
        
        references = []
        target_text = match.group(1) if match else text
        
        matches = re.finditer(r"(IS\s+\d+(?:\s*\([^)]+\))?(?:\s*:\s*\d{4})?)\s+([^\n]+)", target_text)
        for m in matches:
            ref_code = m.group(1).strip()
            ref_desc = m.group(2).strip()
            references.append({
                "relation_type": "Normative Reference",
                "related_is_number": ref_code,
                "title_or_description": ref_desc
            })
            
        return references[:15]

bis_extractor = BISExtractorService()