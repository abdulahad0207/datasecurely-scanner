#!/usr/bin/env bash
set -euo pipefail

echo "=== Deploying datasecurely Scanner ==="
git pull origin main

echo "Building and starting Docker containers..."
docker compose build --pull
docker compose up -d --remove-orphans

echo "Checking API health..."
sleep 5
curl -f http://localhost:8000/health || (echo "Deployment failed health check!" && exit 1)

echo "Deployment successful."
