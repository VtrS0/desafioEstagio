Backend (FastAPI)
-------------------

Run locally:

1. Set environment variables: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS`.
2. Install dependencies: `pip install fastapi uvicorn psycopg2-binary pydantic`
3. Start server: `uvicorn backend.main:app --reload --port 8000`

Routes:
- `GET /api/operadoras?page=&limit=&q=` - paginated list (offset-based)
- `GET /api/operadoras/{cnpj}` - details
- `GET /api/operadoras/{cnpj}/despesas` - history
- `GET /api/estatisticas` - aggregated stats (in-memory cache)

Trade-offs and choices documented in root README.
