"""
Agent 4 (UI/UX) — Central Configuration

All environment-specific settings and tunable constants live here.
Values are read from environment variables (.env) with safe defaults,
so the service runs in any environment without code changes.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Agent-specific .env first, then repo-root fallback (existing env vars win)
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# ── Server ───────────────────────────────────────────────
PORT = int(os.getenv("PORT", "8004"))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]

# ── LLM (OpenRouter) ─────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
LLM_MODEL = os.getenv("AGENT4_LLM_MODEL", "qwen/qwen3-coder")
LLM_TEMPERATURE = float(os.getenv("AGENT4_LLM_TEMPERATURE", "0.2"))
PLANNER_MAX_TOKENS = int(os.getenv("AGENT4_PLANNER_MAX_TOKENS", "1800"))
GENERATOR_MAX_TOKENS = int(os.getenv("AGENT4_GENERATOR_MAX_TOKENS", "4096"))

# ── Evaluation / refinement ──────────────────────────────
SCORE_THRESHOLD = int(os.getenv("AGENT4_SCORE_THRESHOLD", "85"))
MAX_REFINEMENT_ITERATIONS = int(os.getenv("AGENT4_MAX_ITERATIONS", "5"))
WEAK_SUBMETRIC_THRESHOLD = int(os.getenv("AGENT4_WEAK_SUBMETRIC_THRESHOLD", "2"))
WCAG_REFINE_TRIGGER = int(os.getenv("AGENT4_WCAG_REFINE_TRIGGER", "70"))

# Composite weights (ISO 9241-11 / Nielsen / WCAG 2.2) — must sum to 1.0
WEIGHT_ISO = float(os.getenv("AGENT4_WEIGHT_ISO", "0.30"))
WEIGHT_NIELSEN = float(os.getenv("AGENT4_WEIGHT_NIELSEN", "0.30"))
WEIGHT_WCAG = float(os.getenv("AGENT4_WEIGHT_WCAG", "0.40"))
assert abs(WEIGHT_ISO + WEIGHT_NIELSEN + WEIGHT_WCAG - 1.0) < 1e-9, \
    "Composite weights must sum to 1.0"

# ── axe-core runner ──────────────────────────────────────
NODE_BIN = os.getenv("NODE_BIN", "node")
AXE_TIMEOUT = int(os.getenv("AGENT4_AXE_TIMEOUT", "45"))