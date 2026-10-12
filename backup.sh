#!/bin/bash

# PastExam online backup script (services keep running)
# Usage: ./backup.sh
#
# PostgreSQL is dumped with pg_dump, which reads a consistent snapshot while the database
# keeps serving requests. RustFS objects are exported over the S3 API as plain files, so the
# backup does not depend on the storage engine's on-disk format.

set -e

BACKUP_DIR="./backup"
DATE=$(date +%Y%m%d-%H%M%S)
COMPOSE_FILE="${COMPOSE_FILE:-docker/docker-compose.yml}"
RCLONE_IMAGE="rclone/rclone:1.75.1"

set -a
. docker/.env
set +a

mkdir -p $BACKUP_DIR

echo "Starting online backup..."
echo "Backup time: $DATE"

# Dump the database before exporting objects, so every archive row in the dump has its object
echo "Backing up PostgreSQL database..."
docker compose -f $COMPOSE_FILE exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > $BACKUP_DIR/postgres-$DATE.dump
echo "PostgreSQL backup completed"

echo "Backing up RustFS objects..."
RUSTFS_CONTAINER=$(docker inspect -f '{{.Name}}' $(docker compose -f $COMPOSE_FILE ps -q rustfs) | sed 's#^/##')
NETWORK=$(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}' $RUSTFS_CONTAINER)
docker run --rm --network $NETWORK --user "$(id -u):$(id -g)" \
    -v $(pwd)/$BACKUP_DIR:/backup \
    -e RCLONE_CONFIG_RUSTFS_TYPE=s3 \
    -e RCLONE_CONFIG_RUSTFS_PROVIDER=Other \
    -e RCLONE_CONFIG_RUSTFS_ENDPOINT=http://$RUSTFS_CONTAINER:9000 \
    -e RCLONE_CONFIG_RUSTFS_ACCESS_KEY_ID="$RUSTFS_ACCESS_KEY" \
    -e RCLONE_CONFIG_RUSTFS_SECRET_ACCESS_KEY="$RUSTFS_SECRET_KEY" \
    $RCLONE_IMAGE copy rustfs: /backup/rustfs-$DATE
tar cf $BACKUP_DIR/rustfs-$DATE.tar -C $BACKUP_DIR rustfs-$DATE
rm -rf $BACKUP_DIR/rustfs-$DATE
echo "RustFS backup completed"

echo "All backups completed! Backup files located at: $BACKUP_DIR"
echo "Backup file list:"
ls -la $BACKUP_DIR/*$DATE*
