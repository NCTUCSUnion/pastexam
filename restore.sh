#!/bin/bash

# Docker 還原腳本
# 使用方法: ./restore.sh [backup_date]
# 例如: ./restore.sh 20241225-143022

set -e

BACKUP_DIR="./backup"
BACKUP_DATE=$1

if [ -z "$BACKUP_DATE" ]; then
    echo "使用方法: $0 [backup_date]"
    echo "可用的備份："
    ls -la $BACKUP_DIR/ | grep -E "\.(sql|tar\.gz)$" | head -10
    exit 1
fi

echo "開始還原 Docker 容器資料..."
echo "還原日期: $BACKUP_DATE"

# 確保容器停止
echo "停止容器..."
docker compose down

# 還原 Volume 資料
echo "還原 Docker Volumes..."

# 還原 PostgreSQL Volume
if [ -f "$BACKUP_DIR/postgres-volume-$BACKUP_DATE.tar.gz" ]; then
    echo "還原 PostgreSQL volume..."
    docker volume rm pastexam-postgres-data 2>/dev/null || true
    docker volume create pastexam-postgres-data
    docker run --rm -v pastexam-postgres-data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar xzf /backup/postgres-volume-$BACKUP_DATE.tar.gz -C /data
    echo "PostgreSQL volume 還原完成"
fi

# 還原 MinIO Volume
if [ -f "$BACKUP_DIR/minio-volume-$BACKUP_DATE.tar.gz" ]; then
    echo "還原 MinIO volume..."
    docker volume rm pastexam-minio-data 2>/dev/null || true
    docker volume create pastexam-minio-data
    docker run --rm -v pastexam-minio-data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar xzf /backup/minio-volume-$BACKUP_DATE.tar.gz -C /data
    echo "MinIO volume 還原完成"
fi



echo "還原完成！現在可以啟動服務："
echo "docker compose up -d"
