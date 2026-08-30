import json
from pathlib import Path


class ReferenceLoader:
    """
    Loads expert/reference evaluation data for a research test case.

    Expected structure:

    evaluation/
    └── references/
        └── <case_id>/
            ├── requirements.json
            ├── class.json
            ├── sequence.json
            └── er.json
    """

    def __init__(self):
        self.references_dir = (
            Path(__file__).resolve().parent / "references"
        )

    def load_case(self, case_id: str) -> dict:
        case_dir = self.references_dir / case_id

        if not case_dir.exists():
            raise FileNotFoundError(
                f"Reference case not found: {case_id}"
            )

        return {
            "case_id": case_id,
            "requirements": self._load_json(
                case_dir / "requirements.json"
            ),
            "class": self._load_json(
                case_dir / "class.json"
            ),
            "sequence": self._load_json(
                case_dir / "sequence.json"
            ),
            "er": self._load_json(
                case_dir / "er.json"
            ),
        }

    def _load_json(self, file_path: Path) -> dict:
        if not file_path.exists():
            raise FileNotFoundError(
                f"Reference file not found: {file_path}"
            )

        try:
            with file_path.open(
                "r",
                encoding="utf-8"
            ) as file:
                return json.load(file)

        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON in reference file: {file_path}"
            ) from exc