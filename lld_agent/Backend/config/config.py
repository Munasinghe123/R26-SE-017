import os
from dotenv import load_dotenv


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GENERATION_MODEL_1 = "llama-3.3-70b-versatile"
EXPERT_MODEL = "llama-3.3-70b-versatile"

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
