#!/bin/bash

# Docker 備份腳本
# 使用方法: ./backup.sh

set -e

# 設定變數
BACKUP_DIR="./backup"
DATE=$(date +%Y%m%d-%H%M%S)
PROJECT_NAME="pastexam"

# 創建備份目錄
mkdir -p $BACKUP_DIR

echo "開始備份 Docker 容器資料..."
echo "備份時間: $DATE"

# 停止容器以確保資料一致性
echo "停止容器以確保備份資料一致性..."
docker compose -f docker/docker-compose.yml down

# 備份 Volume 資料
echo "備份 Docker Volumes..."

# PostgreSQL Volume 備份
if docker volume ls --format "{{.Name}}" | grep -q "pastexam-postgres-data"; then
    echo "備份 PostgreSQL volume..."
    docker run --rm -v pastexam-postgres-data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/postgres-volume-$DATE.tar.gz -C /data .
    echo "PostgreSQL volume 備份完成"
fi

# MinIO Volume 備份
if docker volume ls --format "{{.Name}}" | grep -q "pastexam-minio-data"; then
    echo "備份 MinIO volume..."
    docker run --rm -v pastexam-minio-data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/minio-volume-$DATE.tar.gz -C /data .
    echo "MinIO volume 備份完成"
fi

echo "所有備份已完成！備份檔案位於: $BACKUP_DIR"
echo "備份檔案列表:"
ls -la $BACKUP_DIR/*$DATE*

echo "重新啟動容器..."
docker compose -f docker/docker-compose.yml up -d

