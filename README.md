# LightRAG Stack (Docker Compose)

Local stack for running [LightRAG](https://github.com/HKUDS/LightRAG) with dedicated storage backends:
- `PostgreSQL` (metadata and KV)
- `Neo4j` (graph)
- `Qdrant` (vector index)

## Architecture

```mermaid
flowchart LR
    U["Client / Browser"] --> A["LightRAG API :9621"]
    A --> P["PostgreSQL :5432"]
    A --> N["Neo4j :7687"]
    A --> Q["Qdrant :6333"]
    N --> NB["Neo4j Browser :7474"]
    Q --> QW["Qdrant UI :6333/dashboard"]
```

## Quick Start

1. Prepare environment variables:
   ```bash
   cp .env.example .env
   ```
2. Fill in secrets in `.env`:
   - `LLM_BINDING_API_KEY`
   - `EMBEDDING_BINDING_API_KEY`
   - `POSTGRES_PASSWORD`
   - `NEO4J_PASSWORD` (must match `NEO4J_AUTH` in `docker-compose.yml`)
3. Start services:
   ```bash
   docker compose up -d
   ```
4. Verify everything is running:
   ```bash
   docker compose ps
   ```

## Endpoints

- LightRAG API: `http://localhost:9621`
- Neo4j Browser: `http://localhost:7474`
- Qdrant REST/UI: `http://localhost:6333`
- PostgreSQL: `localhost:5432`

## Data Layout

```text
data/
├── lightrag/
│   ├── inputs/        # source documents for indexing
│   └── rag_storage/   # LightRAG working files
├── neo4j/             # Neo4j data
├── postgres/          # PostgreSQL data
└── qdrant/            # Qdrant data
```

## Useful Commands

Start:
```bash
docker compose up -d
```

LightRAG logs:
```bash
docker compose logs -f lightrag
```

Restart one service:
```bash
docker compose restart lightrag
```

Stop:
```bash
docker compose down
```

Stop and remove volumes (warning: deletes data):
```bash
docker compose down -v
```

## Configuration

Main variables in `.env`:
- `HOST`, `PORT` - LightRAG host and port
- `INPUT_DIR`, `WORKING_DIR` - paths inside the LightRAG container
- `LLM_*` - generation model and endpoint settings
- `EMBEDDING_*` - embedding model and endpoint settings
- `LIGHTRAG_*_STORAGE` - storage backend selection
- `POSTGRES_*`, `NEO4J_*`, `QDRANT_*` - external service connection settings

## Security

- Do not commit `.env` to the repository.
- Replace all `change_me_*` passwords with strong values.
- If secrets were ever committed, rotate API keys immediately.

## Common Issues

`LightRAG does not start due to database readiness`:
- Wait 10-20 seconds, then check logs:
  ```bash
  docker compose logs --tail=200 postgres neo4j qdrant lightrag
  ```

`Neo4j authentication error`:
- Verify `NEO4J_PASSWORD` in `.env` matches `NEO4J_AUTH` in `docker-compose.yml`.

`No responses from LLM/Embeddings`:
- Verify API keys and endpoint availability for `LLM_BINDING_HOST` and `EMBEDDING_BINDING_HOST`.

## License

See the official repositories for licenses of used container images and the LightRAG project.
