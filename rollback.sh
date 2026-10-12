#!/bin/bash

# PastExam rollback script: run the images CI built for an earlier commit
# Usage: ./rollback.sh <commit>   (from the repo root, as the deploy user)
# Example: sudo -u deploy ./rollback.sh a1103d6
#
# Only the backend and frontend images are switched; compose files and nginx config
# stay at the current checkout. The next deploy from main replaces the images again.

set -e

COMPOSE_FILE="${COMPOSE_FILE:-docker/docker-compose.yml}"
IMAGE="ghcr.io/nctucsunion/pastexam"

if [ -z "$1" ]; then
    echo "Usage: $0 <commit>"
    echo "Recent commits on main:"
    git log --oneline -10 origin/main
    exit 1
fi

# Image tags use the full commit hash
SHA=$(git rev-parse --verify "$1^{commit}")

echo "Rolling back to $SHA..."
for service in backend frontend; do
    docker pull "$IMAGE:$service-$SHA"
    docker tag "$IMAGE:$service-$SHA" "$IMAGE:$service"
done

docker compose -f $COMPOSE_FILE up -d
# nginx caches upstream IPs, which change when containers are recreated
docker compose -f $COMPOSE_FILE restart nginx

echo "Rollback completed! Running images from $SHA"
