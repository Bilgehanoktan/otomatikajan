# from sqlalchemy.orm import Session
from typing import Any, List
import uuid
# from libs.db.models.core_models import Project, ProjectStatus
from services.orchestration.fleet.fleet_scheduler import FleetScheduler

class MultiProjectController:
    def __init__(self, db: Any):
        self.db = db
        self.scheduler = FleetScheduler(db)

    def start_project_batch(self, project_ids: List[uuid.UUID]):
        """Attempts to schedule multiple projects at once."""
        results = {}
        for pid in project_ids:
            success = self.scheduler.schedule_project(pid)
            results[str(pid)] = "scheduled" if success else "deferred"
        return results

    def pause_project(self, project_id: uuid.UUID):
        project = self.db.get(Project, project_id)
        if project:
            project.status = ProjectStatus.PAUSED
            self.db.commit()

    def resume_project(self, project_id: uuid.UUID):
        project = self.db.get(Project, project_id)
        if project and project.status == ProjectStatus.PAUSED:
            # Re-schedule to ensure agents are still available or allocate new ones
            success = self.scheduler.schedule_project(project_id)
            return success
        return False

    def cancel_project(self, project_id: uuid.UUID):
        project = self.db.get(Project, project_id)
        if project:
            project.status = ProjectStatus.CANCELLED
            self.scheduler.release_project_agents(project_id, success=False)
            self.db.commit()

    def complete_project(self, project_id: uuid.UUID):
        project = self.db.get(Project, project_id)
        if project:
            project.status = ProjectStatus.COMPLETED
            self.scheduler.release_project_agents(project_id, success=True)
            self.db.commit()

    def fail_project(self, project_id: uuid.UUID):
        project = self.db.get(Project, project_id)
        if project:
            project.status = ProjectStatus.FAILED
            self.scheduler.release_project_agents(project_id, success=False)
            self.db.commit()

    def process_pending_queue(self):
        """Phase 12.2: Starvation prevention mechanism."""
        from sqlalchemy import select
        from libs.db.base import utcnow
        
        pending_projects = self.db.scalars(
            select(Project)
            .where(Project.status == ProjectStatus.PENDING)
        ).all()
        
        now = utcnow()
        def calculate_score(p: Project):
            from datetime import timezone
            created_at = p.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            wait_hours = (now - created_at).total_seconds() / 3600.0
            return p.priority_level + (wait_hours * 10.0)
            
        pending_projects.sort(key=calculate_score, reverse=True)
        
        results = {}
        for p in pending_projects:
            success = self.scheduler.schedule_project(p.id)
            results[str(p.id)] = "scheduled" if success else "deferred"
            if not success:
                # If budget/resources hit limits, maybe stop processing further
                pass
        return results
