import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

from Services.umlService import UMLService  # noqa: E402


class CloudinaryRenderingTests(unittest.TestCase):
    def test_build_rendered_response_uses_cloudinary_url_instead_of_local_pngs(self):
        parsed_json = {
            "class_diagram": {"classes": [], "relationships": []},
            "sequence_diagrams": [],
            "er_diagram": {"entities": [], "relationships": []},
        }

        with patch("Services.umlService.requests.get") as mock_get, \
             patch("Services.umlService.upload_png_to_cloudinary", return_value="https://res.cloudinary.com/demo/class.png") as mock_upload, \
             patch.object(UMLService, "_persist_diagrams") as mock_persist:
            mock_get.return_value.status_code = 200
            mock_get.return_value.content = b"fake-png"

            response = UMLService._build_rendered_response(parsed_json, validation_report={}, iterations_used=1, project_id=15)

        self.assertEqual(response["cloudinary_urls"]["class"], "https://res.cloudinary.com/demo/class.png")
        self.assertEqual(response["pngs"]["class"], "https://res.cloudinary.com/demo/class.png")
        self.assertIn("plantuml", response)
        self.assertGreaterEqual(mock_upload.call_count, 2)
