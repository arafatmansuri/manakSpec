import re

def parse_bis_features(full_text: str):
    """
    Parses IS number, publication year, amendments, scheme types, 
    and normative references directly from document text.
    """
    # 1. Extract IS Number & Publication Year (e.g., IS 456 : 2000)
    is_match = re.search(r'IS\s+(\d+)(?:\s*:\s*(\d{4}))?', full_text)
    is_number = f"IS {is_match.group(1)}" if is_match else "UNKNOWN_IS"
    pub_year = int(is_match.group(2)) if is_match and is_match.group(2) else 2023

    # 2. Extract Scope section
    scope_text = ""
    if "1 SCOPE" in full_text.upper():
        start = full_text.upper().find("1 SCOPE")
        scope_text = full_text[start:start + 2000]
    elif "FOREWORD" in full_text.upper():
        start = full_text.upper().find("FOREWORD")
        scope_text = full_text[start:start + 2000]
    else:
        scope_text = full_text[:1500]

    # 3. Detect Mandatory Certification & Specific Scheme Types
    upper_text = full_text.upper()
    is_mandatory = "QUALITY CONTROL ORDER" in upper_text or "MANDATORY" in upper_text
    
    scheme_type = "Standard Inspection"
    if "HALLMARK" in upper_text:
        scheme_type = "Hallmarking Scheme"
    elif "COMPULSORY REGISTRATION" in upper_text or "CRS" in upper_text:
        scheme_type = "Compulsory Registration Scheme (CRS)"
    elif "SCHEME - I" in upper_text or "PRODUCT CERTIFICATION" in upper_text:
        scheme_type = "BIS Product Certification (ISI Mark)"

    # 4. Extract Amendments
    amendments = []
    amendment_matches = re.findall(r'AMENDMENT\s+NO\.\s*(\d+)(?:\s+([A-Z]+\s+\d{4}))?', upper_text)
    for match in amendment_matches:
        amendments.append({
            "amendment_no": int(match[0]),
            "description": f"Amendment No. {match[0]}"
        })

    # 5. Extract Normative References
    normative_refs = list(set(re.findall(r'IS\s+\d+', full_text)))
    if is_number in normative_refs:
        normative_refs.remove(is_number)

    return {
        "is_number": is_number,
        "title": f"Indian Standard Specification for {is_number}",
        "publication_year": pub_year,
        "scope_text": scope_text.strip(),
        "is_mandatory_qco": is_mandatory,
        "scheme_type": scheme_type,
        "amendments": amendments,
        "normative_references": normative_refs
    }