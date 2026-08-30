from fastapi import APIRouter, HTTPException
import os

from Controllers.umlController import UMLController
from schemas.umlSchema import GenerateRequest

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    return {
        "status": "healthy",
        "llm_provider": "groq",
        "rag_enabled": False,
        "kroki_url": "",
        "version": "1.0",
    }


@router.post("/generate")
def generate_uml(request: GenerateRequest):
    return UMLController.generate(request)


@router.post("/generate/sample/{sample_id}")
def generate_sample(sample_id: int):
    sample_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "data",
            f"sample{sample_id}.txt",
        )
    )
    if not os.path.exists(sample_path):
        raise HTTPException(status_code=404, detail="Sample not found")

    return UMLController.generate_sample(sample_id)