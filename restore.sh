#!/bin/bash

# PastExam backup restore script
# Usage: ./restore.sh [backup_date]
# Example: ./restore.sh 20241225-143022
#
# Restores backups made by backup.sh. Only backend and worker are stopped while restoring;
# the database and RustFS stay up so the data can be loaded through them.
#
# The current data is backed up first (skip with SKIP_BACKUP=1), and the database is
# replaced in a single transaction, so a failed restore leaves it exactly as it was.
# Set FORCE=1 to skip the confirmation prompt.

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

echo "This replaces the current database and/or files with the backup from $BACKUP_DATE."
[ -f "$DB_DUMP" ] || echo "Warning: no database dump for $BACKUP_DATE, only files will be restored."
[ -f "$OBJECTS_TAR" ] || echo "Warning: no file archive for $BACKUP_DATE, only the database will be restored."
if [ "$FORCE" != "1" ]; then
    read -r -p "Type 'restore' to continue: " answer
    if [ "$answer" != "restore" ]; then
        echo "Aborted"
        exit 1
    fi
fi

if [ "$SKIP_BACKUP" != "1" ]; then
    echo "Backing up the current data first..."
    if ! ./backup.sh; then
        echo "Backup of the current data failed; nothing was restored."
        echo "Run with SKIP_BACKUP=1 to restore anyway."
        exit 1
    fi
fi

# Services stay stopped if a step fails; say how to bring them back
trap 'echo "Restore failed. Start the services again with: docker compose -f $COMPOSE_FILE up -d"' ERR

echo "Starting data restore..."
echo "Restore date: $BACKUP_DATE"

echo "Stopping backend and worker..."
docker compose -f $COMPOSE_FILE stop backend worker
docker compose -f $COMPOSE_FILE up -d --wait db rustfs

if [ -f "$DB_DUMP" ]; then
    echo "Restoring PostgreSQL database..."
    # Recreate the schema instead of pg_restore --clean, which cannot drop tables added
    # after the backup was taken. Everything runs in one transaction: any error rolls the
    # database back to its current state.
    {
        echo "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
        docker compose -f "$COMPOSE_FILE" exec -T db pg_restore --no-owner -f - < "$DB_DUMP"
    } | docker compose -f "$COMPOSE_FILE" exec -T db \
        psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 --single-transaction -q
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
