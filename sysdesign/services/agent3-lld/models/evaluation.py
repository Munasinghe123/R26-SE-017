from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Project
    project_id = Column(
        Integer,
        ForeignKey("lld_projects.id"),
        nullable=False,
        index=True
    )

    # Generation run
    generation_run_id = Column(
        Integer,
        ForeignKey("generation_runs.id"),
        nullable=False,
        index=True
    )

    # Candidate being evaluated
    candidate_id = Column(
        Integer,
        ForeignKey("candidates.id"),
        nullable=False,
        index=True
    )

    # Specific diagram being evaluated
    diagram_id = Column(
        Integer,
        ForeignKey("diagrams.id"),
        nullable=False,
        index=True
    )
    # reference, requirement, expert, combined
    evaluation_type = Column(
        String(50),
        nullable=False,
        default="default"
    )

    # Evaluation scores
    coverage_score = Column(
        Float,
        nullable=True
    )

    correctness_score = Column(
        Float,
        nullable=True
    )

    naming_score = Column(
        Float,
        nullable=True
    )

    structure_score = Column(
        Float,
        nullable=True
    )

    consistency_score = Column(
        Float,
        nullable=True
    )

    overdesign_score = Column(
        Float,
        nullable=True
    )

    syntax_score = Column(
        Float,
        nullable=True
    )

    precision_score = Column(
        Float,
        nullable=True
    )

    recall_score = Column(
        Float,
        nullable=True
    )

    f1_score = Column(
        Float,
        nullable=True
    )

    requirement_coverage_score = Column(
        Float,
        nullable=True
    )

    overall_score = Column(
        Float,
        nullable=True
    )

    # Evaluation model information
    model_name = Column(
        String(150),
        nullable=True
    )

    provider = Column(
        String(100),
        nullable=True
    )

    # Evaluation iteration
    iteration = Column(
        Integer,
        nullable=False,
        default=1
    )

    # Evaluation feedback
    feedback = Column(
        Text,
        nullable=True
    )

    # Detailed evaluation results
    evaluation_details = Column(
        Text,
        nullable=True
    )

    # Evaluation confidence
    confidence_score = Column(
        Float,
        nullable=True
    )

    # Model usage
    input_tokens = Column(
        Integer,
        nullable=True
    )

    output_tokens = Column(
        Integer,
        nullable=True
    )

    total_tokens = Column(
        Integer,
        nullable=True
    )

    # Evaluation execution time
    latency_ms = Column(
        Integer,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )