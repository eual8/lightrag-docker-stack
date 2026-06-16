#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"

echo "Stopping LightRAG stack..."
docker compose down --remove-orphans

echo "Deleting old LightRAG/PostgreSQL/Neo4j records..."
rm -rf \
  data/lightrag/rag_storage \
  data/lightrag/inputs/__enqueued__ \
  data/postgres \
  data/neo4j/data

echo "Recreating empty storage directories..."
mkdir -p \
  data/lightrag/rag_storage \
  data/lightrag/inputs \
  data/postgres \
  data/neo4j/data

echo "Done. Starting again..."

docker compose up -d
