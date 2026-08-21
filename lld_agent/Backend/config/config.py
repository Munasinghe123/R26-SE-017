import os
from dotenv import load_dotenv


load_dotenv()

def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

USE_CANDIDATE_PIPELINE = _env_bool("USE_CANDIDATE_PIPELINE")
GENERATION_PROVIDER = os.getenv("GENERATION_PROVIDER", os.getenv("LLM_PROVIDER", "groq"))
GENERATION_MODEL_1 = "llama-3.3-70b-versatile"
EXPERT_PROVIDER = os.getenv("EXPERT_PROVIDER", "groq")
EXPERT_MODEL = "llama-3.3-70b-versatile"

CANDIDATE_1_PROVIDER = os.getenv("CANDIDATE_1_PROVIDER", GENERATION_PROVIDER)
CANDIDATE_1_MODEL = os.getenv("CANDIDATE_1_MODEL", GENERATION_MODEL_1)
CANDIDATE_1_TEMPERATURE = float(os.getenv("CANDIDATE_1_TEMPERATURE", "0"))
CANDIDATE_1_MAX_TOKENS = int(os.getenv("CANDIDATE_1_MAX_TOKENS", "3500"))

MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))

# Backward-compatible config values used elsewhere
MAX_RETRY_ITERATIONS = int(os.getenv("MAX_RETRY_ITERATIONS", str(MAX_ITERATIONS)))
CONSISTENCY_SCORE_THRESHOLD = float(os.getenv("CONSISTENCY_SCORE_THRESHOLD", "0.85"))

# Prompt profile controls
PROMPT_PROFILE = os.getenv("PROMPT_PROFILE", "")
MAX_REQUIREMENT_DESCRIPTION_CHARS = int(
    os.getenv("MAX_REQUIREMENT_DESCRIPTION_CHARS", "900")
)

# Prompt size controls
MAX_VALIDATION_ERRORS = int(os.getenv("MAX_VALIDATION_ERRORS", "6"))
MAX_ERROR_BLOCK_CHARS = int(os.getenv("MAX_ERROR_BLOCK_CHARS", "1800"))
MAX_ERROR_MESSAGE_CHARS = int(os.getenv("MAX_ERROR_MESSAGE_CHARS", "200"))
MAX_ERROR_SUGGESTION_CHARS = int(os.getenv("MAX_ERROR_SUGGESTION_CHARS", "160"))

MAX_EXPERT_GUIDANCE_CHARS = int(os.getenv("MAX_EXPERT_GUIDANCE_CHARS", "800"))
MAX_RETRY_ERRORS = int(os.getenv("MAX_RETRY_ERRORS", "3"))
MAX_RETRY_ERROR_CHARS = int(os.getenv("MAX_RETRY_ERROR_CHARS", "100"))
MAX_RETRY_GUIDANCE_CHARS = int(os.getenv("MAX_RETRY_GUIDANCE_CHARS", "150"))
MAX_RETRY_REQUIREMENT_DESCRIPTION_CHARS = int(
    os.getenv("MAX_RETRY_REQUIREMENT_DESCRIPTION_CHARS", "120")
)
