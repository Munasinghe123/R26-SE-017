"""Alembic env.py — reads NEON_DATABASE_URL from .env at repo root."""
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

# ── Load .env from repo root (two dirs up: infra/alembic → root) ──────────
_here = Path(__file__).resolve().parent
_root = _here.parent.parent
load_dotenv(_root / ".env")

config = context.config
fileConfig(config.config_file_name, disable_existing_loggers=False)

# ── Inject Neon URL into config so alembic.ini %(NEON_DATABASE_URL)s works ─
neon_url = os.environ.get("NEON_DATABASE_URL", "")
if not neon_url:
    raise RuntimeError("NEON_DATABASE_URL not set. Copy .env.example → .env")
config.set_main_option("NEON_DATABASE_URL", neon_url)

target_metadata = None


def run_migrations_offline() -> None:
    url = config.get_main_option("NEON_DATABASE_URL")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        {"sqlalchemy.url": neon_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
