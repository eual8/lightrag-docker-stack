# LightRAG Stack (Docker Compose)

Local stack for running [LightRAG](https://github.com/HKUDS/LightRAG) with dedicated storage backends:
- `PostgreSQL` with `pgvector` (metadata, KV, document status, and vector index)
- `Neo4j` (graph)

## Architecture

```mermaid
flowchart LR
    U["Client / Browser"] --> A["LightRAG API :9621"]
    A --> P["PostgreSQL + pgvector :5432"]
    A --> N["Neo4j :7687"]
    N --> NB["Neo4j Browser :7474"]
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
- PostgreSQL: `localhost:5432`

## Data Layout

```text
data/
├── lightrag/
│   ├── inputs/        # source documents for indexing
│   └── rag_storage/   # LightRAG working files
├── neo4j/             # Neo4j data
└── postgres/          # PostgreSQL + pgvector data
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
- `POSTGRES_*`, `NEO4J_*` - external service connection settings

This stack uses `PGVectorStorage` for vectors. Switching from another vector backend, such as Qdrant, requires a clean reindex; LightRAG does not migrate vector data between storage implementations.

## Security

- Do not commit `.env` to the repository.
- Replace all `change_me_*` passwords with strong values.
- If secrets were ever committed, rotate API keys immediately.

## Common Issues

`LightRAG does not start due to database readiness`:
- Wait 10-20 seconds, then check logs:
  ```bash
  docker compose logs --tail=200 postgres neo4j lightrag
  ```

`Neo4j authentication error`:
- Verify `NEO4J_PASSWORD` in `.env` matches `NEO4J_AUTH` in `docker-compose.yml`.

`No responses from LLM/Embeddings`:
- Verify API keys and endpoint availability for `LLM_BINDING_HOST` and `EMBEDDING_BINDING_HOST`.

## License

See the official repositories for licenses of used container images and the LightRAG project.
