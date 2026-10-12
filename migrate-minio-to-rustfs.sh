#!/bin/bash

# PastExam MinIO -> RustFS object migration script
# Usage: ./migrate-minio-to-rustfs.sh [backup_date]
# Example: ./migrate-minio-to-rustfs.sh                   (migrate from the live pastexam-minio-data volume)
#          ./migrate-minio-to-rustfs.sh 20251217-122036   (migrate from ./backup/minio-volume-<date>.tar.gz)
#
# RustFS cannot read MinIO's on-disk format, so a temporary MinIO server is started
# on the old data and every bucket is copied into RustFS over the S3 API with mc mirror.

set -e

BACKUP_DIR="./backup"
BACKUP_DATE=$1
COMPOSE_FILE="${COMPOSE_FILE:-docker/docker-compose.yml}"
SRC_VOLUME="pastexam-minio-data"
SRC_CONTAINER="pastexam-minio-migrate-src"
# The official image is no longer pullable, but it is usually still cached on the host.
SRC_IMAGE="${SRC_IMAGE:-quay.io/minio/minio:RELEASE.2025-09-07T16-13-09Z}"
if ! docker image inspect "$SRC_IMAGE" >/dev/null 2>&1; then
    SRC_IMAGE="pgsty/minio:RELEASE.2026-08-04T00-00-00Z"
fi

set -a
. docker/.env
set +a
# The old MinIO root credentials, falling back to the RustFS ones if docker/.env was already renamed.
SRC_ACCESS_KEY="${MINIO_ROOT_USER:-$RUSTFS_ACCESS_KEY}"
SRC_SECRET_KEY="${MINIO_ROOT_PASSWORD:-$RUSTFS_SECRET_KEY}"

echo "Starting MinIO -> RustFS migration..."
echo "Source image: $SRC_IMAGE"

echo "Stopping containers to ensure migration data consistency..."
docker compose -f $COMPOSE_FILE down

if [ -n "$BACKUP_DATE" ]; then
    BACKUP_FILE="$BACKUP_DIR/minio-volume-$BACKUP_DATE.tar.gz"
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "Backup file not found: $BACKUP_FILE"
        exit 1
    fi
    echo "Restoring $BACKUP_FILE into a temporary volume..."
    SRC_VOLUME="pastexam-minio-migrate-src"
    docker volume rm $SRC_VOLUME 2>/dev/null || true
    docker volume create $SRC_VOLUME
    docker run --rm -v $SRC_VOLUME:/data -v $(pwd)/$BACKUP_DIR:/backup alpine:3.22 tar xzf /backup/minio-volume-$BACKUP_DATE.tar.gz -C /data
fi

if ! docker volume ls --format "{{.Name}}" | grep -qx "$SRC_VOLUME"; then
    echo "Source volume not found: $SRC_VOLUME"
    exit 1
fi

echo "Starting RustFS..."
docker compose -f $COMPOSE_FILE up -d --wait rustfs
DST_CONTAINER=$(docker inspect -f '{{.Name}}' $(docker compose -f $COMPOSE_FILE ps -q rustfs) | sed 's#^/##')
NETWORK=$(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}' $DST_CONTAINER)

echo "Starting temporary MinIO on $SRC_VOLUME..."
docker rm -f $SRC_CONTAINER 2>/dev/null || true
docker run -d --name $SRC_CONTAINER --network $NETWORK \
    -e MINIO_ROOT_USER="$SRC_ACCESS_KEY" -e MINIO_ROOT_PASSWORD="$SRC_SECRET_KEY" \
    -v $SRC_VOLUME:/data $SRC_IMAGE server /data
trap 'docker rm -f $SRC_CONTAINER >/dev/null 2>&1 || true' EXIT

mc() {
    docker exec $SRC_CONTAINER mc "$@"
}

# Prints "<key> <size> <md5>" for every object. Multipart ETags are not content MD5s
# (and mc mirror may re-upload as single part), so those objects are hashed directly.
object_checksums() {
    mc ls --recursive --json $1 | sed -E 's/.*"size":([0-9]+),"key":"([^"]*)".*"etag":"([^"]*)".*/\2 \1 \3/' | sort |
    while read -r KEY SIZE ETAG; do
        case "$ETAG" in
            *-*) ETAG=$(mc cat "$1/$KEY" | md5sum | cut -d' ' -f1) ;;
        esac
        echo "$KEY $SIZE $ETAG"
    done
}

until mc ready local >/dev/null 2>&1; do sleep 1; done
mc alias set src http://127.0.0.1:9000 "$SRC_ACCESS_KEY" "$SRC_SECRET_KEY" >/dev/null
mc alias set dst http://$DST_CONTAINER:9000 "$RUSTFS_ACCESS_KEY" "$RUSTFS_SECRET_KEY" >/dev/null

BUCKETS=$(mc ls src | awk '{print $NF}' | sed 's#/$##')
if [ -z "$BUCKETS" ]; then
    echo "No buckets found in source"
    exit 1
fi

for BUCKET in $BUCKETS; do
    echo "Mirroring bucket $BUCKET..."
    mc mb --ignore-existing dst/$BUCKET
    mc mirror --overwrite src/$BUCKET dst/$BUCKET > /dev/null

    echo "Verifying bucket $BUCKET..."
    DIFF=$(diff <(object_checksums src/$BUCKET) <(object_checksums dst/$BUCKET) || true)
    if [ -n "$DIFF" ]; then
        echo "Bucket $BUCKET differs after mirroring:"
        echo "$DIFF"
        exit 1
    fi
    mc ls --recursive --summarize src/$BUCKET | tail -2 | sed 's/^/  source: /'
    mc ls --recursive --summarize dst/$BUCKET | tail -2 | sed 's/^/  rustfs: /'
done

docker rm -f $SRC_CONTAINER >/dev/null
if [ -n "$BACKUP_DATE" ]; then
    docker volume rm $SRC_VOLUME >/dev/null
    echo "Migration completed!"
else
    echo "Migration completed! The old $SRC_VOLUME volume is kept and can be removed manually once verified."
fi

echo "Restarting containers..."
docker compose -f $COMPOSE_FILE up -d
