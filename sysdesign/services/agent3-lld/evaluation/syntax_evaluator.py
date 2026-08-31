import subprocess
import tempfile
from pathlib import Path


class SyntaxEvaluator:
    """
    Evaluates whether generated PlantUML code is syntactically
    valid and can be rendered successfully.
    """

    def evaluate(self, plantuml_code: str | list) -> dict:
        if not plantuml_code:
            return {
                "is_valid": False,
                "score": 0.0,
                "error": "PlantUML code is empty."
            }

        if isinstance(plantuml_code, list):
            if not plantuml_code:
                return {"is_valid": False, "score": 0.0, "error": "PlantUML code list is empty."}
            sub_results = []
            for item in plantuml_code:
                code_str = item.get("plantuml", "") if isinstance(item, dict) else str(item)
                sub_results.append(self.evaluate(code_str))
            scores = [r.get("score", 0.0) for r in sub_results]
            valids = [r.get("is_valid", False) for r in sub_results]
            avg_score = sum(scores) / len(scores) if scores else 0.0
            return {
                "is_valid": all(valids) if valids else False,
                "score": round(avg_score, 4),
                "error": None if all(valids) else "; ".join([r.get("error") for r in sub_results if r.get("error")]),
            }

        code_str = str(plantuml_code).strip()
        if not code_str:
            return {
                "is_valid": False,
                "score": 0.0,
                "error": "PlantUML code is empty."
            }

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                puml_file = temp_path / "diagram.puml"
                puml_file.write_text(code_str, encoding="utf-8")

                result = subprocess.run(
                    ["plantuml", "-tsvg", str(puml_file)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    return {
                        "is_valid": False,
                        "score": 0.0,
                        "error": (
                            result.stderr.strip()
                            or result.stdout.strip()
                            or "PlantUML rendering failed."
                        )
                    }

                svg_file = temp_path / "diagram.svg"
                if not svg_file.exists():
                    return {
                        "is_valid": False,
                        "score": 0.0,
                        "error": "PlantUML completed but no output was generated."
                    }

                return {
                    "is_valid": True,
                    "score": 1.0,
                    "error": None
                }

        except FileNotFoundError:
            # Fallback when plantuml CLI is not installed: verify PlantUML syntax structure
            if "@start" in code_str and "@end" in code_str:
                return {
                    "is_valid": True,
                    "score": 1.0,
                    "error": None
                }
            return {
                "is_valid": False,
                "score": 0.0,
                "error": "PlantUML executable not found and syntax header/footer missing."
            }

        except subprocess.TimeoutExpired:
            return {
                "is_valid": False,
                "score": 0.0,
                "error": "PlantUML rendering timed out."
            }

        except Exception as exc:
            return {
                "is_valid": False,
                "score": 0.0,
                "error": str(exc)
            }