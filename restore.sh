#!/bin/bash

# PastExam backup restore script
# Usage: ./restore.sh [backup_date]
# Example: ./restore.sh 20241225-143022
#
# Restores backups made by backup.sh. Only backend and worker are stopped while restoring;
# the database and RustFS stay up so the data can be loaded through them.

set -e

BACKUP_DIR="./backup"
BACKUP_DATE=$1
COMPOSE_FILE="${COMPOSE_FILE:-docker/docker-compose.yml}"
RCLONE_IMAGE="rclone/rclone:1.75.1"

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 [backup_date]"
    echo "Available backups:"
    ls -la $BACKUP_DIR/ | grep -E "\.(dump|tar)$" | head -10
    exit 1
fi

DB_DUMP="$BACKUP_DIR/postgres-$BACKUP_DATE.dump"
OBJECTS_TAR="$BACKUP_DIR/rustfs-$BACKUP_DATE.tar"
if [ ! -f "$DB_DUMP" ] && [ ! -f "$OBJECTS_TAR" ]; then
    echo "No backup found for $BACKUP_DATE"
    exit 1
fi

set -a
. docker/.env
set +a

echo "Starting data restore..."
echo "Restore date: $BACKUP_DATE"

echo "Stopping backend and worker..."
docker compose -f $COMPOSE_FILE stop backend worker
docker compose -f $COMPOSE_FILE up -d --wait db rustfs

if [ -f "$DB_DUMP" ]; then
    echo "Restoring PostgreSQL database..."
    docker compose -f $COMPOSE_FILE exec -T db pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner < $DB_DUMP
    echo "PostgreSQL restore completed"
fi

if [ -f "$OBJECTS_TAR" ]; then
    echo "Restoring RustFS objects..."
    tar xf $OBJECTS_TAR -C $BACKUP_DIR
    RUSTFS_CONTAINER=$(docker inspect -f '{{.Name}}' $(docker compose -f $COMPOSE_FILE ps -q rustfs) | sed 's#^/##')
    NETWORK=$(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}' $RUSTFS_CONTAINER)
    # sync makes each bucket match the backup exactly, removing objects uploaded after it
    docker run --rm --network $NETWORK --user "$(id -u):$(id -g)" \
        -v $(pwd)/$BACKUP_DIR:/backup \
        -e RCLONE_CONFIG_RUSTFS_TYPE=s3 \
        -e RCLONE_CONFIG_RUSTFS_PROVIDER=Other \
        -e RCLONE_CONFIG_RUSTFS_ENDPOINT=http://$RUSTFS_CONTAINER:9000 \
        -e RCLONE_CONFIG_RUSTFS_ACCESS_KEY_ID="$RUSTFS_ACCESS_KEY" \
        -e RCLONE_CONFIG_RUSTFS_SECRET_ACCESS_KEY="$RUSTFS_SECRET_KEY" \
        $RCLONE_IMAGE sync /backup/rustfs-$BACKUP_DATE rustfs:
    rm -rf $BACKUP_DIR/rustfs-$BACKUP_DATE
    echo "RustFS restore completed"
fi

echo "Restarting services..."
docker compose -f $COMPOSE_FILE up -d
# nginx caches upstream IPs, which change when backend is recreated
docker compose -f $COMPOSE_FILE restart nginx

echo "Restore completed!"
