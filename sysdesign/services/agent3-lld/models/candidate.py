from sqlalchemy import  Column, Integer, String, Boolean, Float, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)

    generation_run_id = Column(
        Integer,
        ForeignKey("generation_runs.id"),
        nullable=False,
        index=True
    )

    candidate_number = Column(
        Integer,
        nullable=False
    )

    provider = Column(
        String(100),
        nullable=True
    )

    model_name = Column(
        String(150),
        nullable=False
    )

    status = Column(
        String(50),
        nullable=False,
        default="generated"
    )

    # Expert selected candidate
    is_selected = Column(
        Boolean,
        nullable=False,
        default=False
    )

    # Expert review info
    expert_score = Column(
        Float,
        nullable=True
    )

    expert_confidence = Column(
        Float,
        nullable=True
    )

    expert_reason = Column(
        Text,
        nullable=True
    )

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

    # Generation performance
    latency_ms = Column(
        Integer,
        nullable=True
    )

    fallback_used = Column(
        Boolean,
        nullable=False,
        default=False
    )

    repair_attempts = Column(
        Integer,
        nullable=False,
        default=0
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )