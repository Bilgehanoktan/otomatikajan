# Rollback & Recovery Playbook

## Database Recovery
If database integrity is lost or corruption is detected:
1. **Stop Services**: `docker-compose stop`
2. **Find Last Backup**: Check `backups/` directory (created by `backup_db.bat`).
3. **Restore**: Run `scripts/production/restore_db.bat` and follow prompts.
4. **Verify**: Run `scripts/production/verify_db_schema.py`.

## Workflow Roleback
To revert a specific workflow to a previous state:
1. Locate the `Project.id` in the Control Plane.
2. In the "Replay" panel, identify the last successful `step_id`.
3. Use the **Manual Override** tool to set `Project.status = 'PENDING'`.
4. Trigger **Replay** starting from the determined `step_id`.

## Service Recovery
If a container stays in `restarting` state:
1. `docker-compose logs <service_name>`
2. Check for missing environment variables.
3. If code related, revert the last Git commit using standard CI/CD procedure.
