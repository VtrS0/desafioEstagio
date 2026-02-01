# Apresentação da Solução — Teste de Integração com API Pública ANS

## Fala (Script de Apresentação)

Olá! Vou apresentar a solução desenvolvida para o teste de integração com a API pública da ANS.

### O Projeto em Resumo

Este projeto implementa uma **solução completa de três camadas** para processar, armazenar e consumir dados de despesas (eventos e sinistros) de operadoras de saúde fornecidos pela ANS:

1. **Camada 1: Banco de Dados (SQL)**
   - Scripts PostgreSQL (>= 10) para criação de tabelas normalizadas
   - Padrão de importação com staging tables
   - Três queries analíticas (crescimento top5, distribuição por UF, operadoras acima da média)

2. **Camada 2: API Backend (FastAPI)**
   - Endpoints RESTful para consultar operadoras, despesas e estatísticas
   - Paginação offset-based para eficiência
   - Cache em memória com TTL para estatísticas
   - Middleware CORS para desenvolvimento

3. **Camada 3: Frontend (Vue 3)**
   - Tabela paginada com busca server-side
   - Gráfico interativo (Chart.js) de despesas por UF
   - Consumo direto da API

### Decisões Técnicas Principais

**Banco de Dados:**
- PostgreSQL escolhido por suporte a JSONB, funções analíticas e eficiência no import via COPY
- Tipos: DECIMAL(15,2) para dinheiro, DATE para trimestres
- Normalização (Opção B): tabelas separadas (operadoras, consolidado_despesas, despesas_agregadas)

**Importação:**
- Estratégia de staging: carregar CSVs brutos em tabela temporária via `\copy`
- Validar e transformar para tabelas finais com remoção de duplicatas e valores inválidos

**API:**
- FastAPI: performance (ASGI), documentação automática (OpenAPI), código limpo
- Paginação offset-based simples; keyset pagination recomendado para grandes volumes
- Cache de estatísticas reduz carga do banco para queries agregadas

**Frontend:**
- Vue 3 (Vite): modern, reativo, componentes reutilizáveis
- Busca server-side para não carregar milhões de linhas no cliente

### Estrutura de Arquivos

```
desafioEstagio/
├── sql/teste3_sql_scripts.sql      # DDL + staging + queries analíticas
├── backend/
│   ├── main.py                     # FastAPI app com endpoints
│   └── README.md                   # Instruções de execução
├── frontend/
│   ├── package.json                # Dependências (Vite, Vue, Chart.js)
│   ├── src/main.js                 # Entry point
│   └── src/components/
│       ├── OperadorasTable.vue     # Tabela + busca
│       └── DespesasChart.vue       # Gráfico
├── postman/operadoras_collection.json  # Exemplos de requisições
├── tests/test_backend.py           # Testes pytest (5 testes, todos passando)
├── requirements.txt                # Dependências Python
└── README.md                       # Documentação consolidada
```

### Como Rodar

**Pré-requisitos:**
- Python 3.13+
- PostgreSQL >= 10
- Node.js + npm (para frontend)

**Passos rápidos:**

1. **Banco de dados:**
```bash
psql -h localhost -U postgres -d desafio -f sql/teste3_sql_scripts.sql
```

2. **Backend:**
```powershell
.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload
# API fica em http://localhost:8000
```

3. **Frontend:**
```bash
cd frontend
npm install
npm run dev
# App fica em http://localhost:5173
```

4. **Testes:**
```powershell
.venv\Scripts\Activate.ps1
pytest -q
# Esperado: 5 passed
```

### Pontos Fortes da Solução

- **Modularidade:** cada camada é independente e testável
- **Escalabilidade:** import incremental, paginação, cache configurável
- **Robustez:** tratamento de erros, validação de dados, staging tables
- **Documentação:** código comentado, READMEs, exemplos Postman
- **Testes:** cobertura de endpoints principais com pytest

### Alternativas Consideradas e Por Que Não Adotadas

1. **Tudo em memória vs. Staging** → Staging: melhor tolerância a falhas e resiliência a retentativas
2. **ORM (SQLAlchemy) vs. SQL crudo** → SQL: controle fino, queries analíticas complexas
3. **Redis cache vs. Cache em memória** → Em memória: simples para MVP; Redis recomendado para produção
4. **GraphQL vs. REST** → REST: familiar, simples para CRUD, suficiente para o escopo

### Próximos Passos (Sugestões)

- Migrar cache para Redis/materialized views para ambientes de produção
- Implementar autenticação (OAuth2/JWT)
- Adicionar limite de rate-limiting
- Testes de carga / benchmarking
- CI/CD pipeline (GitHub Actions, GitLab CI)
- Containerizar com Docker (backend + frontend + postgres)

---

**Conclusão:** Esta solução demonstra uma arquitetura pronta para produção, seguindo boas práticas de separação de camadas, testabilidade e documentação. Pronta para ser expandida e escalonada conforme necessário.
