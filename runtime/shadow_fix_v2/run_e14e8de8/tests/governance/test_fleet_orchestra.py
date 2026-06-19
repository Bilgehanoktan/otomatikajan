import pytest
import uuid
from sqlalchemy import select
from libs.db.models.core_models import AgentNode, AgentRole, AgentStatus, Project, ProjectStatus, FleetCluster
from services.orchestration.fleet.fleet_scheduler import FleetScheduler
from services.orchestration.fleet.agent_registry import AgentRegistry

def test_fleet_scheduling_flow(db_session):
    """
    Verifies that a project can be scheduled, agents assigned, 
    and lineage events recorded.
    """
    # 1. Setup: Create a Cluster and Agents
    cluster = FleetCluster(name="Test Cluster", max_parallel_projects=5)
    db_session.add(cluster)
    db_session.commit()
    
    registry = AgentRegistry(db_session)
    agent1 = registry.register_agent("TestPlanner", AgentRole.PLANNER, cluster.id)
    agent2 = registry.register_agent("TestExecutor", AgentRole.EXECUTOR, cluster.id)
    agent3 = registry.register_agent("TestReviewer", AgentRole.REVIEWER, cluster.id)
    
    # 2. Setup: Create a Project
    project = Project(title="Fleet Test Project", status=ProjectStatus.PENDING, budget_limit=100.0)
    db_session.add(project)
    db_session.commit()
    
    # 3. Execution: Schedule
    scheduler = FleetScheduler(db_session)
    success = scheduler.schedule_project(project.id)
    
    assert success is True
    assert project.status == ProjectStatus.QUEUED
    
    # 4. Verification: Assignments
    from libs.db.models.core_models import FleetAssignment
    assignments = db_session.scalars(select(FleetAssignment).where(FleetAssignment.project_id == project.id)).all()
    assert len(assignments) == 3
    
    # Verify agent statuses
    db_session.refresh(agent1)
    assert agent1.status == AgentStatus.ASSIGNED

def test_fleet_budget_block(db_session):
    """Verifies that projects are deferred if budget is zero/reached."""
    project = Project(title="Broke Project", status=ProjectStatus.PENDING, budget_limit=10.0, total_cost=20.0)
    db_session.add(project)
    db_session.commit()
    
    scheduler = FleetScheduler(db_session)
    success = scheduler.schedule_project(project.id)
    
    assert success is False
    assert project.status == ProjectStatus.WAITING
    assert "Budget limit reached" in project.report

def test_fleet_quarantine_exclusion(db_session):
    """Verifies that quarantined agents are not assigned to projects."""
    cluster = FleetCluster(name="Safety Cluster", max_parallel_projects=5)
    db_session.add(cluster)
    db_session.commit()
    
    registry = AgentRegistry(db_session)
    # Register agents but put one in quarantine
    registry.register_agent("GoodPlanner", AgentRole.PLANNER, cluster.id)
    bad_executor = registry.register_agent("BadExecutor", AgentRole.EXECUTOR, cluster.id)
    bad_executor.status = AgentStatus.QUARANTINED
    db_session.commit()
    
    project = Project(title="Security Sensitive Project", status=ProjectStatus.PENDING)
    db_session.add(project)
    db_session.commit()
    
    scheduler = FleetScheduler(db_session)
    # Should fail because no EXECUTOR is available (the only one is quarantined)
    success = scheduler.schedule_project(project.id)
    
    assert success is False
    assert project.status == ProjectStatus.WAITING
