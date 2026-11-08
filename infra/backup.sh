#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="/var/backups/datasecurely"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "${BACKUP_DIR}"

echo "=== Backing up datasecurely data (${TIMESTAMP}) ==="

# Backup local reports and data volumes
if [ -d "./storage" ]; then
    tar -czf "${BACKUP_DIR}/storage_${TIMESTAMP}.tar.gz" ./storage
    echo "Storage directory backed up."
fi

# Remove backups older than 14 days
find "${BACKUP_DIR}" -type f -name "*.tar.gz" -mtime +14 -delete
echo "Backup complete."
