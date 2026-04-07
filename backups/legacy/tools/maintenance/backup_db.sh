#!/bin/bash

# AI Company Database Backup Script
# Usage: ./backup_db.sh

# Load environment variables from .env.production
if [ -f .env.production ]; then
    export $(grep -v '^#' .env.production | xargs)
else
    echo ".env.production file not found!"
    exit 1
fi

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql.gz"
RETENTION_DAYS=7

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

echo "Starting database backup..."

# Run pg_dump via docker exec
# Note: Using the container name 'db' as defined in docker-compose.prod.yml
docker exec db pg_dump -U "${DB_USER}" ai_company | gzip > "${BACKUP_FILE}"

if [ $? -eq 0 ]; then
    echo "Backup successful: ${BACKUP_FILE}"
    
    # Clean up old backups (older than RETENTION_DAYS)
    find "${BACKUP_DIR}" -type f -name "db_backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
    echo "Old backups cleaned up (Retention: ${RETENTION_DAYS} days)."
else
    echo "Backup failed!"
    exit 1
fi
