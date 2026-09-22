CREATE TABLE "chat_messages" (
	"id" serial PRIMARY KEY,
	"session_id" uuid,
	"role" varchar(20) NOT NULL,
	"content" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE "chat_sessions" (
	"session_id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"user_id" varchar(100) NOT NULL,
	"created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
	"updated_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE "indian_standards" (
	"is_number" varchar(50) PRIMARY KEY,
	"title" text NOT NULL,
	"publication_year" integer NOT NULL,
	"status" varchar(20) DEFAULT 'Active',
	"scope_text" text,
	"is_mandatory_qco" boolean DEFAULT false,
	"scheme_type" varchar(50),
	"scope_embedding" vector(768),
	"latest_amendment" varchar(100),
	"amendment_details" text,
	CONSTRAINT "indian_standards_status_check" CHECK (((status)::text = ANY ((ARRAY['Active'::character varying, 'Reaffirmed'::character varying, 'Withdrawn'::character varying, 'Under Revision'::character varying])::text[])))
);
CREATE TABLE "standard_relations" (
	"id" serial PRIMARY KEY,
	"parent_is_number" varchar(50),
	"relation_type" varchar(50) NOT NULL,
	"related_is_number" varchar(50),
	"title_or_description" text NOT NULL,
	"amendment_no" integer,
	"amendment_year" integer
);
CREATE UNIQUE INDEX "chat_messages_pkey" ON "chat_messages" ("id");
CREATE INDEX "idx_chat_messages_created" ON "chat_messages" ("created_at");
CREATE INDEX "idx_chat_messages_session" ON "chat_messages" ("session_id");
CREATE UNIQUE INDEX "chat_sessions_pkey" ON "chat_sessions" ("session_id");
CREATE INDEX "idx_chat_sessions_user" ON "chat_sessions" ("user_id");
CREATE INDEX "idx_is_mandatory_qco" ON "indian_standards" ("is_mandatory_qco");
CREATE INDEX "idx_is_scope_embedding" ON "indian_standards" USING hnsw ("scope_embedding");
CREATE INDEX "idx_is_status" ON "indian_standards" ("status");
CREATE UNIQUE INDEX "indian_standards_pkey" ON "indian_standards" ("is_number");
CREATE INDEX "idx_relations_parent" ON "standard_relations" ("parent_is_number");
CREATE INDEX "idx_relations_related" ON "standard_relations" ("related_is_number");
CREATE INDEX "idx_relations_type" ON "standard_relations" ("relation_type");
CREATE UNIQUE INDEX "standard_relations_pkey" ON "standard_relations" ("id");
ALTER TABLE "chat_messages" ADD CONSTRAINT "chat_messages_session_id_fkey" FOREIGN KEY ("session_id") REFERENCES "chat_sessions"("session_id") ON DELETE CASCADE;
ALTER TABLE "standard_relations" ADD CONSTRAINT "standard_relations_parent_is_number_fkey" FOREIGN KEY ("parent_is_number") REFERENCES "indian_standards"("is_number") ON DELETE CASCADE;