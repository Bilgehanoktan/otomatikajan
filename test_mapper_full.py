from db.models import SovereignGoal, Project, Base, CEOSuggestedTask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_mapper():
    try:
        # First, ensure mappers are initialized
        from sqlalchemy.orm import configure_mappers
        configure_mappers()
        print("Mappers configured successfully!")
        
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        print("Table creation successful!")

        # Test relationships
        Session = sessionmaker(bind=engine)
        session = Session()

        goal = SovereignGoal(title="Master AI", vision_statement="AI")
        project = Project(title="Code Gen", goal=goal)
        
        session.add(goal)
        session.add(project)
        session.commit()
        
        print(f"Goal: {goal.title}, Project Count: {len(goal.projects)}")
        assert len(goal.projects) == 1
        print("Relationship test passed!")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mapper()
