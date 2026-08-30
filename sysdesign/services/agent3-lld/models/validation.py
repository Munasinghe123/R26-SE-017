from sqlalchemy import Column, Integer, Boolean, Float, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from database import Base


class Validation(Base):
    __tablename__ = "validations"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Project this validation belongs to
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

    # Candidate that was validated
    candidate_id = Column(
        Integer,
        ForeignKey("candidates.id"),
        nullable=False,
        index=True
    )

    # Diagram being validated
    diagram_id = Column(
        Integer,
        ForeignKey("diagrams.id"),
        nullable=False,
        index=True
    )

    # Overall validation result
    is_valid = Column(
        Boolean,
        nullable=False,
        default=False
    )

    # Validation statistics
    total_checks = Column(
        Integer,
        nullable=False,
        default=0
    )

    passed_checks = Column(
        Integer,
        nullable=False,
        default=0
    )

    failed_checks = Column(
        Integer,
        nullable=False,
        default=0
    )

    warning_count = Column(
        Integer,
        nullable=False,
        default=0
    )

    error_count = Column(
        Integer,
        nullable=False,
        default=0
    )

    # Validation score
    validation_score = Column(
        Float,
        nullable=True
    )

    # Detailed validation results
    errors = Column(
        Text,
        nullable=True
    )

    warnings = Column(
        Text,
        nullable=True
    )

    # Detailed validation information
    validation_details = Column(
        Text,
        nullable=True
    )

    # Validation iteration
    iteration = Column(
        Integer,
        nullable=False,
        default=1
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )