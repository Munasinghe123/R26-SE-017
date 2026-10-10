"""
HLA Agent — Central Configuration (v2: Style-Aware Evaluation Framework)

All constants, thresholds, weights, and mappings live here.
Nothing is hardcoded anywhere else in the project.

Models are configurable via environment variables — change value and re-run.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present (agent-specific, then root fallback)
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# ──────────────────────────────────────────────
# PATHS
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input"
RESULTS_DIR = BASE_DIR / "results"
WEB_DIR = BASE_DIR / "web"
DB_PATH = RESULTS_DIR / "results.db"

# Ensure results directory exists
RESULTS_DIR.mkdir(exist_ok=True)

# ──────────────────────────────────────────────
# LLM PROVIDER — OpenRouter Only
# ──────────────────────────────────────────────
LLM_PROVIDER = "openrouter"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# ──────────────────────────────────────────────
# MODEL CONFIGURATION — Hot-swappable via .env
# ──────────────────────────────────────────────
OPENROUTER_MODEL_1 = os.getenv(
    "OPENROUTER_MODEL_1",
    "meta-llama/llama-3.1-8b-instruct:free",
)
OPENROUTER_MODEL_2 = os.getenv(
    "OPENROUTER_MODEL_2",
    "qwen/qwen-2.5-7b-instruct:free",
)
OPENROUTER_MODEL_3 = os.getenv(
    "OPENROUTER_MODEL_3",
    "deepseek/deepseek-chat-v3-0324",
)

MODELS = [OPENROUTER_MODEL_1, OPENROUTER_MODEL_2, OPENROUTER_MODEL_3]

# All models route through OpenRouter
PROVIDER_MODELS = {
    "openrouter": MODELS,
}

# ──────────────────────────────────────────────
# GENERATION CONFIGURATION
# ──────────────────────────────────────────────
# Temperature — configurable for research (temperature study)
GENERATION_TEMPERATURE = float(os.getenv("GENERATION_TEMPERATURE", "0.1"))

# Max candidates per model (adaptive: LLM decides 1-3 styles)
MAX_CANDIDATES_PER_MODEL = int(os.getenv("MAX_CANDIDATES_PER_MODEL", "3"))

# For backward compatibility
CANDIDATES_PER_MODEL = MAX_CANDIDATES_PER_MODEL

# Generation seeds for reproducibility
_seeds_str = os.getenv("GENERATION_SEEDS", "42,137,256")
GENERATION_SEEDS = [int(s.strip()) for s in _seeds_str.split(",")]

GENERATION_OPTIONS = {
    "temperature": GENERATION_TEMPERATURE,
    "max_tokens": int(os.getenv("GENERATION_MAX_TOKENS", "4000")),
    "top_p": float(os.getenv("GENERATION_TOP_P", "0.2")),
    "seed": GENERATION_SEEDS[0],  # Default seed; generator may override per-candidate
}

# Temperature sweep values (for research experiment — overridable via .env)
_sweep_str = os.getenv("TEMPERATURE_SWEEP_VALUES", "0.0,0.1,0.3,0.5,0.7,1.0")
TEMPERATURE_SWEEP_VALUES = [float(t.strip()) for t in _sweep_str.split(",")]

# Diagram generation (LLM)
DIAGRAM_MAX_ITERATIONS = int(os.getenv("DIAGRAM_MAX_ITERATIONS", "2"))
DIAGRAM_GENERATION_OPTIONS = {
    "temperature": float(os.getenv("DIAGRAM_TEMPERATURE", "0.1")),
    "max_tokens": int(os.getenv("DIAGRAM_MAX_TOKENS", "2500")),
    "top_p": float(os.getenv("DIAGRAM_TOP_P", "0.2")),
    "seed": int(os.getenv("DIAGRAM_SEED", "42")),
}

# Retry configuration
MAX_GENERATION_RETRIES = 3
MAX_REGENERATION_LOOPS = 0  # Disabled: using Human-in-the-Loop

# ──────────────────────────────────────────────
# ARCHITECTURE STYLES
# Richards & Ford (2020), Newman (2019)
# ──────────────────────────────────────────────
ARCHITECTURE_STYLES = [
    "Layered Architecture",
    "Microservices Architecture",
    "Event-Driven Architecture",
    "Modular Monolith",
    "Pipe-and-Filter Architecture",
]

# Canonical style keys (used internally)
STYLE_KEYS = [
    "layered",
    "microservices",
    "event_driven",
    "modular_monolith",
    "pipe_and_filter",
]

# ──────────────────────────────────────────────
# METRIC WEIGHTS — AHP-derived (preliminary)
# See evaluation/ahp.py for derivation
# CR = 0.013 < 0.10 (consistent)
# These are preliminary. Final weights after expert survey.
# ──────────────────────────────────────────────
WEIGHTS = {
    "RTS":  0.2917,  # Requirement Traceability Score
    "QAC":  0.2194,  # Quality Attribute Coverage
    "CI":   0.1361,  # Coupling Index
    "CoS":  0.1361,  # Cohesion Score
    "SSM1": 0.1361,  # Style-Specific Metric 1
    "SSM2": 0.0806,  # Style-Specific Metric 2
}

# Verify weights sum to 1.0
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, f"Metric weights must sum to 1.0, got {sum(WEIGHTS.values())}"

# ──────────────────────────────────────────────
# METRIC THRESHOLDS (minimum acceptable scores)
# ──────────────────────────────────────────────
THRESHOLDS = {
    "RTS":  0.70,   # At least 70% FR traceability
    "QAC":  0.60,   # At least 60% NFR coverage
    "CI":   0.50,   # Reasonable decoupling
    "CoS":  0.50,   # Reasonable cohesion
    "SSM1": 0.50,   # Reasonable style conformance
    "SSM2": 0.40,   # Minimum style conformance
    "CAS":  0.60,   # Overall acceptance gate
}

# CAS verdict ranges
CAS_ACCEPTED = 0.75
CAS_MARGINAL = 0.60

# ──────────────────────────────────────────────
# SEMANTIC THRESHOLDS (calibratable)
# See evaluation/calibration.py for justification
# ──────────────────────────────────────────────
RTS_THRESHOLD = float(os.getenv("RTS_THRESHOLD", "0.55"))
QAC_THRESHOLD = float(os.getenv("QAC_THRESHOLD", "0.50"))

# ──────────────────────────────────────────────
# LAYER ORDERING (for style-specific metrics)
# Higher number = lower in the stack
# ──────────────────────────────────────────────
DEFAULT_LAYER_ORDER = {
    "presentation":     1,
    "ui":               1,
    "frontend":         1,
    "client":           1,
    "api gateway":      2,
    "gateway":          2,
    "api":              2,
    "application":      3,
    "business logic":   3,
    "business":         3,
    "service":          3,
    "use case":         3,
    "domain":           4,
    "data access":      5,
    "persistence":      5,
    "database":         6,
    "infrastructure":   6,
    "external":         7,
    "integration":      7,
    "messaging":        4,
    "event bus":        4,
    "ports":            3,
    "adapters":         5,
}
