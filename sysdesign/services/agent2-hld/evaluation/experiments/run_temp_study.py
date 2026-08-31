"""
Research Experiment — Temperature Sweep Study

Evaluates candidate architectural diversity and score variance across temperatures:
T ∈ {0.0, 0.1, 0.3, 0.5, 0.7, 1.0}

Measures:
- Candidate parse success rate vs temperature
- Metric variance (std dev of CAS, RTS, QAC across temperatures)
- Architectural diversity (style shifts, component count variation)
"""

import sys
import json
import io
import logging
from pathlib import Path

# Reconfigure stdout for Windows console unicode support
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from config import TEMPERATURE_SWEEP_VALUES, MODELS, INPUT_DIR
from generation.generator import generate_single
from cam.parser import extract_json_from_text, CAMParseError
from evaluation import evaluate_architecture
from prompt.builder import build_architecture_prompt

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TempStudy-Runner")


def run_temperature_experiment(model: str = MODELS[0], sample_file: str | None = None):
    """Run temperature sweep experiment across configured temperature values."""
    if not sample_file:
        sample_file = str(BASE_DIR / "input" / "sample_food_delivery.json")

    with open(sample_file, "r", encoding="utf-8") as f:
        requirements = json.load(f)

    prompt = build_architecture_prompt(requirements, candidate_num=1)
    results = []

    print("\n=======================================================")
    print(f"    RESEARCH EXPERIMENT: TEMPERATURE SWEEP STUDY      ")
    print(f"    Model: {model}")
    print("=======================================================\n")
    print("| Temp (T) | Parse OK | Detected Style | RTS | QAC | CI | CoS | CAS |")
    print("|----------|----------|----------------|-----|-----|----|-----|-----|")

    for temp in TEMPERATURE_SWEEP_VALUES:
        options = {"temperature": temp, "max_tokens": 4000}
        gen_res = generate_single(model, prompt, candidate_num=1, options_override=options)

        if not gen_res.success:
            print(f"| {temp:8.1f} | ❌ Fail   | {'N/A':14s} | -   | -   | -  | -   | -   |")
            results.append({"temperature": temp, "success": False, "scores": None})
            continue

        try:
            json_str = extract_json_from_text(gen_res.raw_text)
            arch = json.loads(json_str)
            scores = evaluate_architecture(arch, requirements)
            style = scores.get("detected_style", "unknown")

            print(
                f"| {temp:8.1f} | ✅ Pass   | {style:14s} | "
                f"{scores['RTS']:.2f} | {scores['QAC']:.2f} | {scores['CI']:.2f} | "
                f"{scores['CoS']:.2f} | {scores['CAS']:.4f} |"
            )
            results.append({
                "temperature": temp,
                "success": True,
                "detected_style": style,
                "scores": scores,
                "component_count": len(arch.get("components", [])),
            })
        except Exception as e:
            print(f"| {temp:8.1f} | ❌ Parse  | {'Unparseable':14s} | -   | -   | -  | -   | -   |")
            results.append({"temperature": temp, "success": False, "error": str(e)})

    return results


if __name__ == "__main__":
    run_temperature_experiment()
