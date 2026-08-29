"""
create_tables.py — Direct DDL execution against Neon Postgres.
Run: python create_tables.py
Creates all 5 tables needed by the R26-SE-017 multi-agent system.
"""

import sys
import os

try:
    import psycopg2
except ImportError:
    print("Installing psycopg2-binary...")
    os.system(f"{sys.executable} -m pip install psycopg2-binary --quiet")
    import psycopg2

NEON_URL = (
    "postgresql://neondb_owner:npg_xu2LWXchSb7U"
    "@ep-dark-mode-az3pl4xm-pooler.c-3.ap-southeast-1.aws.neon.tech"
    "/neondb?sslmode=require"
)

DDL = """
-- Extension for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1. Tenants
CREATE TABLE IF NOT EXISTS tenants (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
INSERT INTO tenants (id, name) VALUES ('dev', 'Development')
ON CONFLICT DO NOTHING;

-- 2. Jobs
CREATE TABLE IF NOT EXISTS jobs (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     TEXT NOT NULL REFERENCES tenants(id),
    created_by    TEXT NOT NULL DEFAULT 'dev-user',
    project_name  TEXT NOT NULL,
    status        TEXT NOT NULL,
    current_stage TEXT,
    input_kind    TEXT NOT NULL DEFAULT 'requirements',
    input_uri     TEXT,
    error         TEXT,
    created_at    TIMESTAMPTZ DEFAULT now(),
    updated_at    TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_jobs_tenant_status ON jobs(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at    ON jobs(created_at DESC);

-- 3. Stage runs (one row per agent per job)
CREATE TABLE IF NOT EXISTS stage_runs (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id         UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    stage          TEXT NOT NULL,
    attempt        INTEGER NOT NULL DEFAULT 1,
    status         TEXT NOT NULL,
    payload        JSONB,
    schema_version TEXT NOT NULL DEFAULT '1.0',
    llm_backend    TEXT,
    duration_ms    INTEGER,
    started_at     TIMESTAMPTZ DEFAULT now(),
    finished_at    TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_stage_runs_job_stage ON stage_runs(job_id, stage);
CREATE INDEX IF NOT EXISTS idx_stage_runs_payload   ON stage_runs USING GIN(payload);

-- 4. Artifacts (file/URI pointers for diagrams, HTML screens, PDFs)
CREATE TABLE IF NOT EXISTS artifacts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id      UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    stage       TEXT NOT NULL,
    kind        TEXT NOT NULL,
    filename    TEXT NOT NULL,
    uri         TEXT NOT NULL,
    mime_type   TEXT NOT NULL,
    size_bytes  INTEGER,
    created_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_artifacts_job_stage ON artifacts(job_id, stage);

-- 5. Architecture candidates (the THESIS DATASET — every HLD run recorded)
CREATE TABLE IF NOT EXISTS architecture_candidates (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id           UUID REFERENCES jobs(id) ON DELETE CASCADE,
    case_study_id    TEXT NOT NULL,
    llm_model        TEXT NOT NULL,
    seed             INTEGER NOT NULL,
    detected_style   TEXT NOT NULL,
    style_confidence NUMERIC(4,3),
    rts              NUMERIC(4,3),
    qac              NUMERIC(4,3),
    ci               NUMERIC(4,3),
    cos              NUMERIC(4,3),
    ssm1             NUMERIC(4,3),
    ssm2             NUMERIC(4,3),
    cas              NUMERIC(4,3) NOT NULL,
    verdict          TEXT NOT NULL,
    rank_position    INTEGER,
    cam              JSONB NOT NULL DEFAULT '{}',
    created_at       TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_arch_cand_case_model ON architecture_candidates(case_study_id, llm_model);
CREATE INDEX IF NOT EXISTS idx_arch_cand_cas         ON architecture_candidates(cas DESC);
"""

def main():
    print(f"Connecting to Neon Postgres...")
    try:
        conn = psycopg2.connect(NEON_URL)
        conn.autocommit = True
        cur = conn.cursor()

        print("Running DDL statements...")
        cur.execute(DDL)

        # Verify tables created
        cur.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)
        tables = [row[0] for row in cur.fetchall()]

        expected = ["architecture_candidates", "artifacts", "jobs", "stage_runs", "tenants"]
        print(f"\n✅ Tables in Neon database:")
        for t in tables:
            marker = "✓" if t in expected else "·"
            print(f"   {marker} {t}")

        missing = [t for t in expected if t not in tables]
        if missing:
            print(f"\n❌ Still missing: {missing}")
            sys.exit(1)
        else:
            print(f"\n✅ All 5 required tables exist in Neon!")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
