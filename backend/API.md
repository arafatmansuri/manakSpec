# ManakSpec Backend API Documentation

An AI-powered recommendation and tender drafting engine for identifying applicable Bureau of Indian Standards (BIS) and Quality Control Orders (QCO) for government and enterprise procurement specifications.

---

## 1. System Overview & Core Capabilities

* **Hybrid Retrieval (Lexical + Semantic)**: Combines dense vector cosine similarity (via PostgreSQL `pgvector` HNSW index on 768-dim embeddings) with exact Indian Standard code matching (`IS XXXX`) and title keyword weighting.
* **Multilingual Input & Regional Understanding**: Accepts procurement scopes in English, Hindi, Tamil, Telugu, Marathi, Bengali, and other regional Indian languages; translates queries into English domain terminology for vector retrieval while providing synthesized explanations in the requested language.
* **Granular Allied Standards Classification**: Automatically categorizes all cross-referenced standards into 6 distinct procurement types:
  1. *Test Methods* (mechanical/chemical testing, sampling, measurement)
  2. *Safety Standards* (fire safety, electric shock, hazard protection)
  3. *Terminology Standards* (glossary, definitions, symbols)
  4. *Installation / Code of Practice* (erection, laying, maintenance guidelines)
  5. *Related Product Standards* (fittings, components, dimensions)
  6. *Normative References* (general normative citations)
* **Multi-Format Tender Document Ingestion**: Ingests procurement scopes and tender specifications from `.pdf`, `.docx`, `.txt`, `.csv`, `.png`, `.jpg`, and `.jpeg` (with OCR fallback supporting `hin+eng`).
* **Zero-Dependency Multi-Format Export**: Generates downloadable schedules in Adobe PDF 1.4 vector format, Microsoft Word `.docx` (OpenXML), Plain Text `.txt`, and Markdown `.md` with targetable `chat_id` / `message_id` support.
* **Stateful Chat History & Auto-Titling**: Threaded conversations in PostgreSQL with auto-titling on the first recommendation turn.

---

## 2. API Endpoints Summary

| HTTP Method | Route | Category | Summary |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | System | Health check for server and database connection pool |
| `POST` | `/api/v1/sessions/` | Sessions | Initialize user and create a new chat session thread |
| `GET` | `/api/v1/sessions/{user_id}` | Sessions | Retrieve all chat sessions for a user (sidebar history) |
| `GET` | `/api/v1/sessions/chat/{session_id}` | Sessions | Retrieve chronological message history for a session |
| `POST` | `/api/v1/standards/recommend` | Recommendations | Primary AI engine for standards recommendation & tender clause drafting |
| `GET` | `/api/v1/standards/export/{identifier}` | Export | Export tender schedule by session or specific `chat_id` (PDF, DOCX, TXT, MD) |
| `GET` | `/api/v1/standards/export/message/{message_id}` | Export | Direct alias to export a specific chat response turn |
| `POST` | `/api/v1/standards/ingest` | Ingestion | Ingest an individual BIS standard or amendment (PDF / JSON) |
| `POST` | `/api/v1/standards/ingest-bulk` | Ingestion | Asynchronously ingest multiple standards or `.zip` archives |
| `GET` | `/api/v1/standards/ingest-job/{job_id}` | Ingestion | Poll status and progress of a background ingestion task |

---

## 3. Detailed Endpoint Documentation

### 3.1 Health Check

#### `GET /health`
Verifies that the FastAPI application is alive and checks whether the async PostgreSQL connection pool is connected.

* **Headers**: None
* **Parameters**: None
* **Response (`200 OK`)**:
```json
{
  "status": "online",
  "database": "connected"
}
```

---

### 3.2 Chat Sessions & History

#### `POST /api/v1/sessions/`
Creates a new chat session in PostgreSQL and ensures the user exists in the `users` table.

* **Request Body** (`application/json`):
  | Field | Type | Required | Default | Description |
  | :--- | :--- | :--- | :--- | :--- |
  | `user_id` | `string` | Optional | Auto-generated UUID | Unique user identifier |
  | `title` | `string` | Optional | `"New Chat"` | Initial session title |

* **Response (`201 Created`)**:
```json
{
  "user_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "session_id": "c3b9d621-8f3a-4a2e-9d2a-4318d1a1b123",
  "title": "New Chat",
  "created_at": "2026-09-24T09:00:00Z"
}
```

---

#### `GET /api/v1/sessions/{user_id}`
Retrieves all historical chat sessions for a given `user_id` ordered by `updated_at DESC` (typically used to populate the UI conversation sidebar).

* **Path Parameters**:
  * `user_id` (`string`, required): UUID of the user.

* **Response (`200 OK`)**:
```json
[
  {
    "session_id": "c3b9d621-8f3a-4a2e-9d2a-4318d1a1b123",
    "title": "IS 16106 - LED Luminaires",
    "created_at": "2026-09-24T08:30:00Z",
    "updated_at": "2026-09-24T08:45:00Z"
  }
]
```

---

#### `GET /api/v1/sessions/chat/{session_id}`
Returns the session title and all chronological messages (`created_at ASC`) for a specific chat thread. Each message includes an integer `message_id`.

* **Path Parameters**:
  * `session_id` (`string`, required): UUID of the chat session.

* **Response (`200 OK`)**:
```json
{
  "session_id": "c3b9d621-8f3a-4a2e-9d2a-4318d1a1b123",
  "title": "IS 16106 - LED Luminaires",
  "messages": [
    {
      "message_id": "42",
      "role": "user",
      "content": "Procurement of 50W LED Street Lights for Smart City project",
      "execution_provider": null,
      "created_at": "2026-09-24T08:30:00Z"
    },
    {
      "message_id": "43",
      "role": "assistant",
      "content": {
        "overview": "...",
        "primary_standards_summary": [],
        "certification_details": {},
        "allied_references": [],
        "tender_clause": {}
      },
      "execution_provider": "Google Gemini API",
      "created_at": "2026-09-24T08:30:05Z"
    }
  ]
}
```
* **Errors**: `404 Not Found` if `session_id` does not exist.

---

### 3.3 AI Recommendations & Tender Drafting

#### `POST /api/v1/standards/recommend`
The primary AI recommendation engine. Accepts natural language prompts (in English or regional Indian languages) and/or uploaded procurement documents (`.pdf`, `.docx`, `.txt`, `.csv`, `.png`, `.jpg`, `.jpeg`).

Executes query expansion, hybrid vector/lexical retrieval, dynamic allied standards classification, and LLM structured synthesis.

* **Content-Type**: `multipart/form-data`
* **Form Parameters**:
  | Field | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `session_id` | `string` | Yes | UUID of the active chat session |
  | `user_id` | `string` | Yes | User identifier |
  | `query_text` | `string` | Optional* | Procurement prompt, scope, or product description (*Must supply `query_text` or `file`) |
  | `file` | `UploadFile` | Optional* | Tender document (`.pdf`, `.docx`, `.txt`, `.csv`, `.png`, `.jpg`, `.jpeg`) |
  | `language` | `string` | Optional | Target response language (e.g. `"Hindi"`, `"English"`, `"Tamil"`) |

* **Response (`200 OK`)**:
```json
{
  "session_id": "c3b9d621-8f3a-4a2e-9d2a-4318d1a1b123",
  "user_id": "user-uuid",
  "detected_language": "Hindi",
  "query_expansion_used": "LED Luminaire Street Lighting IS 16106 IS 10322 Part 5 Sec 3...",
  "execution_provider": "Google Gemini API",
  "allied_references": [
    {
      "parent_is_number": "IS 16106",
      "relation_type": "Test Method",
      "related_is_number": "IS 16108",
      "title_or_description": "Photo-biological safety of lamps and lamp systems",
      "amendment_no": null,
      "amendment_year": null
    }
  ],
  "structured_synthesis": {
    "overview": "Summary of applicable Indian Standards for the procurement scope...",
    "primary_standards_summary": [
      {
        "is_number": "IS 16106:2023",
        "title": "Methods of Electrical and Photometric Measurements of Solid-State Lighting (LED) Products",
        "publication_year": 2023,
        "status": "Active",
        "latest_amendment": "Amendment No. 1 (2024)",
        "amendment_details": "Updated luminous efficacy requirements",
        "scope_text": "Specifies photometric and electrical test procedures...",
        "is_mandatory_qco": true,
        "scheme_type": "CRS Scheme-II",
        "committee_code": "ETD 23",
        "gazette_notice_id": "HQ-PUB/2023/QCO-01",
        "reaffirmation_year": 2024,
        "technical_specifications": { "efficacy_min": "100 lm/W", "cri_min": 70 },
        "similarity_score": 0.942
      }
    ],
    "certification_details": {
      "scheme_name": "Compulsory Registration Scheme (CRS) - Scheme-II",
      "governing_body_or_order": "Ministry of Electronics & Information Technology (MeitY) QCO",
      "mark_type": "Standard Mark (CRS)",
      "requirements": [
        "Manufacturer must register with BIS prior to import or sale",
        "Product must be tested at a BIS-recognized laboratory"
      ]
    },
    "allied_references": [
      {
        "parent_is_number": "IS 16106",
        "relation_type": "Test Method",
        "related_is_number": "IS 16108",
        "title_or_description": "Photo-biological safety of lamps and lamp systems",
        "amendment_no": null,
        "amendment_year": null
      }
    ],
    "tender_clause": {
      "title": "Technical Specification & Standards Compliance Clause",
      "standard_compliance": "The supplier shall strictly comply with IS 16106:2023...",
      "mandatory_cert_clause": "Bidder must possess valid BIS CRS Registration...",
      "technical_specifications": [
        "Luminous Efficacy: Minimum 120 lumens/watt",
        "Surge Protection: Built-in 10 kV surge protection conforming to IS 16106"
      ],
      "testing_and_documentation": "Type test reports from NABL accredited lab to be submitted with bid"
    }
  }
}
```
* **Errors**:
  * `400 Bad Request`: If neither `query_text` nor `file` is provided, or unsupported file extension.
  * `422 Unprocessable Entity`: Document text could not be parsed.
  * `500 Internal Server Error`: Agent execution or LLM provider failure.

---

### 3.4 Tender Specification Export

#### `GET /api/v1/standards/export/{identifier}`
#### `GET /api/v1/standards/export/message/{message_id}`
Exports a generated BIS technical recommendation and model tender clause schedule as a downloadable attachment.

* **Targeting Options**:
  * Pass a **`message_id`** (numeric integer, e.g. `43`) to download that specific response turn.
  * Pass a **`session_id`** (UUID) to download the latest response from that chat session.
  * Pass query parameter `?chat_id=<id>` with a session UUID to target a specific turn.

* **Parameters**:
  | Parameter | In | Type | Required | Default | Description |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `identifier` | Path | `string` | Yes | - | Message ID (`"43"`) OR Session UUID |
  | `chat_id` | Query | `string` | Optional | `null` | Optional explicit message ID to download |
  | `format` | Query | `string` | Optional | `"docx"` | Export format: `"pdf"`, `"docx"`, `"txt"`, or `"md"` |

* **Supported Formats**:
  | Format | File Extension | Content-Type | Details |
  | :--- | :--- | :--- | :--- |
  | `pdf` | `.pdf` | `application/pdf` | Vector PDF (Adobe PDF 1.4) with styled banners, tables, and pagination |
  | `docx` | `.docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | Microsoft Word document with editable tables and XML styles |
  | `txt` | `.txt` | `text/plain; charset=utf-8` | Plain text with ASCII headers for copying into e-procurement portals |
  | `md` | `.md` | `text/markdown; charset=utf-8` | Formatted Markdown schedule |

* **Headers in Response**:
  `Content-Disposition: attachment; filename="<Title>_chat_<id>.<ext>"`

---

### 3.5 Standards Ingestion

#### `POST /api/v1/standards/ingest`
Ingests an individual BIS standard or amendment from a PDF or structured JSON file. Extracts metadata, classifies Annex A references, computes vector embeddings, and upserts into `indian_standards` and `standard_relations`.

* **Content-Type**: `multipart/form-data`
* **Form Parameters**:
  | Field | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `file` | `UploadFile` | Yes | BIS Standard document (`.pdf` or `.json`) |
  | `is_number` | `string` | Optional | Manual override for IS Code (e.g. `"IS 10322"`) |
  | `title` | `string` | Optional | Manual override for Standard Title |
  | `publication_year` | `integer` | Optional | Publication Year |
  | `scope` | `string` | Optional | Scope Description override |
  | `is_mandatory_qco` | `boolean` | Optional | Mandatory QCO flag |
  | `scheme_type` | `string` | Optional | Scheme type (e.g. `"Scheme-I"`, `"CRS"`) |
  | `relation_type` | `string` | Optional | Relation type if amendment (e.g. `"Amendment"`) |
  | `parent_is_number` | `string` | Optional | Parent IS Code if file is an amendment |
  | `technical_specifications_json`| `string` | Optional | JSON string of technical parameters |

* **Response (`201 Created`)**:
```json
{
  "status": "success",
  "type": "Base Standard Upserted",
  "is_number": "IS 16106",
  "title": "Methods of Electrical and Photometric Measurements...",
  "publication_year": 2023,
  "committee_code": "ETD 23",
  "relations_added": 4
}
```

---

#### `POST /api/v1/standards/ingest-bulk`
Accepts multiple `.pdf` or `.json` files, or `.zip` archives containing standards. Decompresses in memory and processes batch ingestion via background worker tasks.

* **Content-Type**: `multipart/form-data`
* **Form Parameters**:
  | Field | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `files` | `List[UploadFile]` | Yes | List of PDF/JSON files or `.zip` archives |

* **Response (`202 Accepted`)**:
```json
{
  "message": "Bulk ingestion job queued successfully.",
  "job_id": "7f09c123-4b67-4e89-b1a2-998877665544",
  "total_files_queued": 15,
  "status_check_url": "/api/v1/standards/ingest-job/7f09c123-4b67-4e89-b1a2-998877665544"
}
```

---

#### `GET /api/v1/standards/ingest-job/{job_id}`
Checks the real-time status and progress of an asynchronous bulk ingestion task.

* **Path Parameters**:
  * `job_id` (`string`, required): UUID of the batch ingestion job.

* **Response (`200 OK`)**:
```json
{
  "job_id": "7f09c123-4b67-4e89-b1a2-998877665544",
  "status": "completed",
  "total_files": 15,
  "processed_files": 15,
  "failed_files": 0,
  "details": [
    {
      "filename": "IS_16106.pdf",
      "status": "success",
      "result": {
        "status": "success",
        "type": "Base Standard Upserted",
        "is_number": "IS 16106"
      }
    }
  ]
}
```

---

## 4. Example Usage & Workflows

### 4.1 Create a Chat Session
```bash
curl -X POST "http://localhost:8000/api/v1/sessions/" \
     -H "Content-Type: application/json" \
     -d '{"title": "Street Lighting Procurement"}'
```

### 4.2 Request Recommendations with Multilingual Text
```bash
curl -X POST "http://localhost:8000/api/v1/standards/recommend" \
     -F "session_id=c3b9d621-8f3a-4a2e-9d2a-4318d1a1b123" \
     -F "user_id=usr-101" \
     -F "query_text=एलईडी स्ट्रीट लाइट और उसके ड्राइवर के लिए तकनीकी मानक" \
     -F "language=Hindi"
```

### 4.3 Request Recommendations with a Tender Document (.pdf or .docx)
```bash
curl -X POST "http://localhost:8000/api/v1/standards/recommend" \
     -F "session_id=c3b9d621-8f3a-4a2e-9d2a-4318d1a1b123" \
     -F "user_id=usr-101" \
     -F "file=@Tender_Specification_Cables.docx"
```

### 4.4 Export Tender Schedule as Vector PDF by `message_id`
```bash
curl -O -J "http://localhost:8000/api/v1/standards/export/message/43?format=pdf"
```

### 4.5 Export Tender Schedule as Word (.docx) by `session_id`
```bash
curl -O -J "http://localhost:8000/api/v1/standards/export/c3b9d621-8f3a-4a2e-9d2a-4318d1a1b123?format=docx"
```
