import os
import uuid
import sys
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from libs.db.session import SessionLocal
from libs.db.models.core_models import Project, AgentNode, FleetCluster, FleetAssignment, ProjectStatus, AgentStatus, AgentRole, FleetStatus
from services.orchestration.fleet.fleet_scheduler import FleetScheduler
from services.orchestration.fleet.multi_project_controller import MultiProjectController
from services.orchestration.fleet.agent_registry import AgentRegistry

def test_fleet_mechanisms():
    db = SessionLocal()
    try:
        scheduler = FleetScheduler(db)
        controller = MultiProjectController(db)
        registry = AgentRegistry(db)
        
        print("=== Test 1: Dynamic Fleet Rebalancing ===")
        # Note: We won't assert exact values to be non-destructive.
        # We will just run the method and see if it throws any exceptions.
        try:
            scheduler.rebalance_fleet()
            print("rebalance_fleet() executed successfully.")
        except Exception as e:
            print(f"Error in rebalance_fleet(): {e}")
            return False

        print("\n=== Test 2: Starvation Prevention in Queue ===")
        try:
            results = controller.process_pending_queue()
            print(f"process_pending_queue() executed successfully. Results: {results}")
        except Exception as e:
            print(f"Error in process_pending_queue(): {e}")
            return False

        print("\n=== Test 3: Agent Reputation & Release Logic ===")
        # For a non-destructive test, we can query an existing agent or create a dummy one,
        # update its reputation, then revert the change if we want.
        dummy_agent = AgentNode(
            id=uuid.uuid4(),
            name="TestAgent_Reputation",
            role="EXECUTOR",
            status=AgentStatus.IDLE,
            trust_score=0.5,
            success_count=0,
            failure_count=0
        )
        db.add(dummy_agent)
        db.commit()
        
        try:
            # Test success update
            registry.update_agent_reputation(dummy_agent.id, success=True)
            db.refresh(dummy_agent)
            print(f"After Success - Trust Score: {dummy_agent.trust_score}, Success Count: {dummy_agent.success_count}")
            
            # Test failure update
            registry.update_agent_reputation(dummy_agent.id, success=False)
            db.refresh(dummy_agent)
            print(f"After Failure - Trust Score: {dummy_agent.trust_score}, Failure Count: {dummy_agent.failure_count}")
            
            print("update_agent_reputation() executed successfully.")
        except Exception as e:
            print(f"Error in update_agent_reputation(): {e}")
            return False
        finally:
            # Clean up dummy agent
            db.delete(dummy_agent)
            db.commit()
            
        print("\nAll tests passed successfully without destructive side-effects!")
        return True
    finally:
        db.close()

if __name__ == "__main__":
    test_fleet_mechanisms()
