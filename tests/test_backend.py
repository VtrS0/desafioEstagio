from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.main import app


class MockCursor:
    def __init__(self, fetchone_result=None, fetchall_result=None):
        self._fe = fetchone_result
        self._fa = fetchall_result or []

    def execute(self, *args, **kwargs):
        return None

    def fetchone(self):
        return self._fe

    def fetchall(self):
        return self._fa


class MockConn:
    def __init__(self, fetchone_result=None, fetchall_result=None):
        self._cursor = MockCursor(fetchone_result, fetchall_result)

    def cursor(self):
        return self._cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_list_operadoras():
    fetchone = {"count": 2}
    fetchall = [
        {"cnpj": "123", "razao_social": "A SA", "nome_fantasia": "A", "uf": "SP"},
        {"cnpj": "456", "razao_social": "B SA", "nome_fantasia": "B", "uf": "RJ"},
    ]
    with patch('backend.main.get_conn', return_value=MockConn(fetchone_result=fetchone, fetchall_result=fetchall)):
        client = TestClient(app)
        r = client.get('/api/operadoras?page=1&limit=10')
        assert r.status_code == 200
        j = r.json()
        assert j['total'] == 2
        assert len(j['data']) == 2


def test_get_operadora_found():
    fetchone = {"cnpj": "123", "razao_social": "A SA", "uf": "SP"}
    with patch('backend.main.get_conn', return_value=MockConn(fetchone_result=fetchone)):
        client = TestClient(app)
        r = client.get('/api/operadoras/123')
        assert r.status_code == 200
        j = r.json()
        assert j['cnpj'] == '123'


def test_get_operadora_not_found():
    with patch('backend.main.get_conn', return_value=MockConn(fetchone_result=None)):
        client = TestClient(app)
        r = client.get('/api/operadoras/000')
        assert r.status_code == 404


def test_operadora_despesas():
    fetchall = [
        {"trimestre_date": "2025-01-01", "despesa_total": "1000.00"},
        {"trimestre_date": "2025-04-01", "despesa_total": "1200.00"},
    ]
    with patch('backend.main.get_conn', return_value=MockConn(fetchall_result=fetchall)):
        client = TestClient(app)
        r = client.get('/api/operadoras/123/despesas')
        assert r.status_code == 200
        j = r.json()
        assert isinstance(j, list)
        assert len(j) == 2


def test_estatisticas():
    # prepare totals (fetchone) and top5 (fetchall)
    totals = {"total": 2200, "media": 1100}
    top5 = [{"cnpj": "123", "total": 1500}, {"cnpj": "456", "total": 700}]
    with patch('backend.main.get_conn', return_value=MockConn(fetchone_result=totals, fetchall_result=top5)):
        client = TestClient(app)
        r = client.get('/api/estatisticas')
        assert r.status_code == 200
        j = r.json()
        assert 'total_despesas' in j
        assert 'top5' in j
