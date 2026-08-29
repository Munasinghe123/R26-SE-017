-- Add detailed evaluation metrics while preserving existing evaluation records.

ALTER TABLE evaluations
    ADD COLUMN IF NOT EXISTS syntax_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS precision_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS recall_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS f1_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS requirement_coverage_score DOUBLE PRECISION;