from sqlalchemy.orm import Session
from typing import List
import uuid
from libs.db.models.core_models import Project, ProjectStatus
from services.orchestration.fleet.fleet_scheduler import FleetScheduler

class MultiProjectController:
    def __init__(self, db: Session):
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
            # TODO: Release agents via assignment_repo
            self.db.commit()
