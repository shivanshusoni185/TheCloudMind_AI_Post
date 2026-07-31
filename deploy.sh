#!/bin/bash
set -e

echo "==> Pulling latest code..."
git pull origin main

echo "==> Building and starting services..."
docker compose up -d --build

echo "==> Done. Status:"
docker compose ps
