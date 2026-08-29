from database import engine, Base

# Import every model so SQLAlchemy registers all tables
from models.project import Project
from models.generation_run import GenerationRun
from models.candidate import Candidate
from models.diagram import Diagram
from models.validation import Validation
from models.evaluation import Evaluation
from models.expert_review import ExpertReview


def initialize_database():
    Base.metadata.create_all(bind=engine)