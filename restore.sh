#!/bin/bash

# PastExam docker backup restore script
# Usage: ./restore.sh [backup_date]
# Example: ./restore.sh 20241225-143022

set -e

BACKUP_DIR="./backup"
BACKUP_DATE=$1

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 [backup_date]"
    echo "Available backups:"
    ls -la $BACKUP_DIR/ | grep -E "\.(sql|tar\.gz)$" | head -10
    exit 1
fi

echo "Starting Docker container data restore..."
echo "Restore date: $BACKUP_DATE"

echo "Stopping containers..."
docker compose -f docker/docker-compose.yml down

echo "Restoring Docker Volumes..."

# Restore PostgreSQL Volume
if [ -f "$BACKUP_DIR/postgres-volume-$BACKUP_DATE.tar.gz" ]; then
    echo "Restoring PostgreSQL volume..."
    docker volume rm pastexam-postgres-data 2>/dev/null || true
    docker volume create pastexam-postgres-data
    docker run --rm -v pastexam-postgres-data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine:3.22 tar xzf /backup/postgres-volume-$BACKUP_DATE.tar.gz -C /data
    echo "PostgreSQL volume restore completed"
fi

# Restore MinIO Volume
if [ -f "$BACKUP_DIR/minio-volume-$BACKUP_DATE.tar.gz" ]; then
    echo "Restoring MinIO volume..."
    docker volume rm pastexam-minio-data 2>/dev/null || true
    docker volume create pastexam-minio-data
    docker run --rm -v pastexam-minio-data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine:3.22 tar xzf /backup/minio-volume-$BACKUP_DATE.tar.gz -C /data
    echo "MinIO volume restore completed"
fi

echo "Restore completed! You can now start the services"