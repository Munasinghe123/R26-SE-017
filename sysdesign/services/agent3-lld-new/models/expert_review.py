from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from database import Base


class ExpertReview(Base):
    __tablename__ = "expert_reviews"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Project being reviewed
    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True
    )

    # Generation run being reviewed
    generation_run_id = Column(
        Integer,
        ForeignKey("generation_runs.id"),
        nullable=False,
        index=True
    )

    # Selected candidate
    selected_candidate_id = Column(
        Integer,
        ForeignKey("candidates.id"),
        nullable=True,
        index=True
    )

    # Scores given to each candidate
    candidate_1_score = Column(
        Float,
        nullable=True
    )

    candidate_2_score = Column(
        Float,
        nullable=True
    )

    candidate_3_score = Column(
        Float,
        nullable=True
    )

    # Expert model information
    model_name = Column(
        String(150),
        nullable=True
    )

    provider = Column(
        String(100),
        nullable=True
    )

    # Expert confidence in the final selection
    confidence_score = Column(
        Float,
        nullable=True
    )

    # Explanation for selecting the candidate
    selection_reason = Column(
        Text,
        nullable=True
    )

    # Complete expert review output
    review_details = Column(
        Text,
        nullable=True
    )

    # Expert review iteration
    iteration = Column(
        Integer,
        nullable=False,
        default=1
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

    # Expert review execution time
    latency_ms = Column(
        Integer,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )