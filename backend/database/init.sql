-- Step 1: Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Step 2: Main Indian Standards Table (Primary Metadata & Scope Vector)
CREATE TABLE IF NOT EXISTS indian_standards (
    is_number VARCHAR(50) PRIMARY KEY,
    title TEXT NOT NULL,
    publication_year INT NOT NULL,
    status VARCHAR(20) DEFAULT 'Active' 
        CHECK (status IN ('Active', 'Reaffirmed', 'Withdrawn', 'Under Revision')),
    scope_text TEXT,
    is_mandatory_qco BOOLEAN DEFAULT FALSE,
    scheme_type VARCHAR(50),
    scope_embedding vector(384) -- 384 dimensions matching BAAI/bge-small-en-v1.5
);

-- HNSW Cosine Distance Vector Index
CREATE INDEX IF NOT EXISTS idx_is_scope_embedding 
ON indian_standards 
USING hnsw (scope_embedding vector_cosine_ops);

-- Additional Metadata B-Tree Indexes
CREATE INDEX IF NOT EXISTS idx_is_status ON indian_standards(status);
CREATE INDEX IF NOT EXISTS idx_is_mandatory_qco ON indian_standards(is_mandatory_qco);

-- Step 3: Normative References & Relationships (Annex A, Amendments, Tests)
CREATE TABLE IF NOT EXISTS standard_relations (
    id SERIAL PRIMARY KEY,
    parent_is_number VARCHAR(50) REFERENCES indian_standards(is_number) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL,
    related_is_number VARCHAR(50),
    title_or_description TEXT NOT NULL,
    amendment_no INT,
    amendment_year INT
);

-- GIN Index on parent standard lookup for fast array JOINs
CREATE INDEX IF NOT EXISTS idx_relations_parent 
ON standard_relations (parent_is_number);
CREATE INDEX IF NOT EXISTS idx_relations_type ON standard_relations(relation_type);
CREATE INDEX IF NOT EXISTS idx_relations_related ON standard_relations(related_is_number);

-- Step 4: Anonymous Session & Chat History Tables
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id);

CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created ON chat_messages(created_at);