import subprocess
import tempfile
from pathlib import Path


class SyntaxEvaluator:
    """
    Evaluates whether generated PlantUML code is syntactically
    valid and can be rendered successfully.
    """

    def evaluate(self, plantuml_code: str) -> dict:
        if not plantuml_code or not plantuml_code.strip():
            return {
                "is_valid": False,
                "score": 0.0,
                "error": "PlantUML code is empty."
            }

        temp_dir = None

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                puml_file = temp_path / "diagram.puml"
                puml_file.write_text(
                    plantuml_code,
                    encoding="utf-8"
                )

                result = subprocess.run(
                    [
                        "plantuml",
                        "-tsvg",
                        str(puml_file)
                    ],
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
            return {
                "is_valid": False,
                "score": 0.0,
                "error": (
                    "PlantUML executable was not found. "
                    "Make sure PlantUML is installed and available in PATH."
                )
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