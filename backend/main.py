"""FastAPI backend for operadoras and despesas (minimal implementation).
Run with: uvicorn backend.main:app --reload
Configure DB via env vars: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional
import time

app = FastAPI(title="Operadoras API")

# Allow CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PARAMS = dict(
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', 5432)),
    dbname=os.getenv('DB_NAME', 'desafio'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASS', ''),
)

def get_conn():
    return psycopg2.connect(cursor_factory=RealDictCursor, **DB_PARAMS)


class PaginatedResponse(BaseModel):
    data: List[dict]
    total: int
    page: int
    limit: int


@app.get('/api/operadoras', response_model=PaginatedResponse)
def list_operadoras(page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), q: Optional[str] = None):
    offset = (page - 1) * limit
    with get_conn() as conn:
        cur = conn.cursor()
        if q:
            q_like = f"%{q}%"
            cur.execute("SELECT count(*) FROM operadoras WHERE cnpj ILIKE %s OR razao_social ILIKE %s", (q_like, q_like))
            total = cur.fetchone()['count']
            cur.execute("SELECT cnpj, razao_social, nome_fantasia, uf FROM operadoras WHERE cnpj ILIKE %s OR razao_social ILIKE %s ORDER BY razao_social LIMIT %s OFFSET %s", (q_like, q_like, limit, offset))
        else:
            cur.execute("SELECT count(*) FROM operadoras")
            total = cur.fetchone()['count']
            cur.execute("SELECT cnpj, razao_social, nome_fantasia, uf FROM operadoras ORDER BY razao_social LIMIT %s OFFSET %s", (limit, offset))
        rows = cur.fetchall()
    return {"data": rows, "total": int(total), "page": page, "limit": limit}


@app.get('/api/operadoras/{cnpj}')
def get_operadora(cnpj: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM operadoras WHERE regexp_replace(cnpj,'[^0-9]','','g') = regexp_replace(%s,'[^0-9]','','g')", (cnpj,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Operadora not found')
    return row


@app.get('/api/operadoras/{cnpj}/despesas')
def operadora_despesas(cnpj: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT trimestre_date, despesa_total FROM consolidado_despesas WHERE regexp_replace(cnpj,'[^0-9]','','g') = regexp_replace(%s,'[^0-9]','','g') ORDER BY trimestre_date",
            (cnpj,)
        )
        rows = cur.fetchall()
    return rows


# Simple in-memory cache for /api/estatisticas with TTL
_cache = {"value": None, "ts": 0}
CACHE_TTL = int(os.getenv('STATS_CACHE_SECONDS', '300'))


@app.get('/api/estatisticas')
def estatisticas(force: bool = False):
    now = time.time()
    if not force and _cache['value'] and now - _cache['ts'] < CACHE_TTL:
        return _cache['value']
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT SUM(despesa_total) as total, AVG(despesa_total) as media FROM consolidado_despesas")
        totals = cur.fetchone()
        cur.execute("SELECT cnpj, SUM(despesa_total) as total FROM consolidado_despesas GROUP BY cnpj ORDER BY total DESC LIMIT 5")
        top5 = cur.fetchall()
    payload = {"total_despesas": totals['total'], "media": float(totals['media']) if totals['media'] is not None else None, "top5": top5}
    _cache['value'] = payload
    _cache['ts'] = now
    return payload


@app.get('/api/estatisticas/uf')
def estatisticas_uf():
    """Return total despesas by UF and mean per operadora in each UF."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT uf, SUM(despesa_total) as total_despesas FROM consolidado_despesas GROUP BY uf ORDER BY total_despesas DESC")
        totals_by_uf = cur.fetchall()
        cur.execute(
            "SELECT uf, AVG(sum_per_operadora) as media_por_operadora FROM (SELECT uf, cnpj, SUM(despesa_total) as sum_per_operadora FROM consolidado_despesas GROUP BY uf, cnpj) s GROUP BY uf ORDER BY media_por_operadora DESC"
        )
        media_por_operadora = cur.fetchall()
    return {"totals_by_uf": totals_by_uf, "media_por_operadora": media_por_operadora}
