#!/bin/bash

# PastExam docker backup script
# Usage: ./backup.sh

set -e

BACKUP_DIR="./backup"
DATE=$(date +%Y%m%d-%H%M%S)
PROJECT_NAME="pastexam"

mkdir -p $BACKUP_DIR

echo "Starting Docker container data backup..."
echo "Backup time: $DATE"

echo "Stopping containers to ensure backup data consistency..."
docker compose -f docker/docker-compose.yml down

echo "Backing up Docker Volumes..."

# PostgreSQL Volume backup
if docker volume ls --format "{{.Name}}" | grep -q "pastexam-postgres-data"; then
    echo "Backing up PostgreSQL volume..."
    docker run --rm -v pastexam-postgres-data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine:3.22 tar czf /backup/postgres-volume-$DATE.tar.gz -C /data .
    echo "PostgreSQL volume backup completed"
fi

# RustFS Volume backup
if docker volume ls --format "{{.Name}}" | grep -q "pastexam-rustfs-data"; then
    echo "Backing up RustFS volume..."
    docker run --rm -v pastexam-rustfs-data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine:3.22 tar czf /backup/rustfs-volume-$DATE.tar.gz -C /data .
    echo "RustFS volume backup completed"
fi

echo "All backups completed! Backup files located at: $BACKUP_DIR"
echo "Backup file list:"
ls -la $BACKUP_DIR/*$DATE*

echo "Restarting containers..."
docker compose -f docker/docker-compose.yml up -d

