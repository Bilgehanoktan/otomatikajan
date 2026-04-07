from packages.persistence.models import SovereignGoal, Project, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_mapper():
    try:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        print("Mapper initialized successfully!")
    except Exception as e:
        print(f"Mapper failed: {e}")

if __name__ == "__main__":
    test_mapper()
