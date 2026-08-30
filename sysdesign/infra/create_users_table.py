import asyncio, os, sys

sys.path.insert(0, 'services/agent1-requirements')
from dotenv import load_dotenv
load_dotenv('.env')
import asyncpg

DDL = """
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'USER',
    created_at    TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE TABLE IF NOT EXISTS projects (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name             TEXT NOT NULL,
    description      TEXT,
    product_owner_id UUID NOT NULL REFERENCES users(id),
    client_id        UUID NOT NULL REFERENCES users(id),
    created_at       TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_projects_owner  ON projects(product_owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_client ON projects(client_id);
"""

async def main():
    url = os.getenv('CONNECTION_STRING') or os.getenv('NEON_DATABASE_URL')
    if not url:
        print('ERROR: CONNECTION_STRING or NEON_DATABASE_URL not set in .env')
        sys.exit(1)
    print('Connecting to Neon Postgres...')
    conn = await asyncpg.connect(url)
    print('Running DDL...')
    await conn.execute(DDL)
    tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
    print('Tables in database:')
    for t in tables:
        print(' -', t['tablename'])
    await conn.close()
    print('Done! users and projects tables ready.')

asyncio.run(main())
