from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from database import Base


class GenerationRun(Base):
    __tablename__ = "generation_runs"

    id = Column(Integer, primary_key=True, index=True)

    # Project that this generation belongs to
    project_id = Column(
        Integer,
        ForeignKey("lld_projects.id"),
        nullable=False,
        index=True
    )

    # Generation status
    status = Column(
        String(50),
        nullable=False,
        default="started"
    )

    # Total number of candidates generated
    total_candidates = Column(
        Integer,
        nullable=False,
        default=3
    )

    # Candidate selected by the expert reviewer
    selected_candidate_id = Column(
        Integer,
        ForeignKey("candidates.id"),
        nullable=True
    )

    # Number of generation/repair iterations
    iterations_used = Column(
        Integer,
        nullable=False,
        default=1
    )

    # Generation timestamps
    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )