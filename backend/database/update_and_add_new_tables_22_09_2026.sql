-- 1. Create New Tables
CREATE TABLE "bis_committees" (
	"committee_code" varchar(50) PRIMARY KEY,
	"committee_name" varchar(255) NOT NULL,
	"created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "gazette_notices" (
	"gazette_notice_id" varchar(100) PRIMARY KEY,
	"publication_date" date NOT NULL,
	"gazette_title" text,
	"created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

-- 2. Update Existing "indian_standards" Table
ALTER TABLE "indian_standards" 
	ADD COLUMN "committee_code" varchar(50),
	ADD COLUMN "gazette_notice_id" varchar(100),
	ADD COLUMN "reaffirmation_year" integer,
	ADD COLUMN "technical_specifications" jsonb DEFAULT '{}'::jsonb,
	ADD COLUMN "created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
	ADD COLUMN "updated_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE "indian_standards" 
	ADD CONSTRAINT "indian_standards_committee_code_fkey" 
	FOREIGN KEY ("committee_code") REFERENCES "bis_committees"("committee_code") ON DELETE SET NULL;

ALTER TABLE "indian_standards" 
	ADD CONSTRAINT "indian_standards_gazette_notice_id_fkey" 
	FOREIGN KEY ("gazette_notice_id") REFERENCES "gazette_notices"("gazette_notice_id") ON DELETE SET NULL;

-- 3. Create Indexes
CREATE INDEX "idx_standards_committee" ON "indian_standards" ("committee_code");
CREATE INDEX "idx_standards_gazette" ON "indian_standards" ("gazette_notice_id");
CREATE INDEX "idx_standards_tech_specs" ON "indian_standards" USING gin ("technical_specifications");