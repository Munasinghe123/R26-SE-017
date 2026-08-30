import os, psycopg2, sys
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("NEON_DATABASE_URL") or os.getenv("CONNECTION_STRING")
if not url:
    print("ERROR: Neither NEON_DATABASE_URL nor CONNECTION_STRING is set.")
    sys.exit(1)

conn = psycopg2.connect(url)
conn.autocommit = True
cur = conn.cursor()

cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
tables = [r[0] for r in cur.fetchall()]

print("TABLES IN NEON:")
for t in tables:
    print(" -", t)

expected = ["architecture_candidates", "artifacts", "jobs", "stage_runs", "tenants"]
missing = [t for t in expected if t not in tables]

if missing:
    print("MISSING:", missing)
    sys.exit(1)
else:
    print("ALL 5 TABLES CONFIRMED IN NEON!")

cur.close()
conn.close()
