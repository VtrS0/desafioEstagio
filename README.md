# Teste de Integração com API Pública ANS - Guia Completo

## 📋 Resumo do Projeto

Este projeto baixa dados de Despesas com Eventos/Sinistros dos últimos 3 trimestres da API da ANS (Agência Nacional de Saúde Suplementar), consolida os dados de múltiplos formatos e gera um arquivo CSV único, tratando automaticamente inconsistências encontradas.

---

## 🎯 Objetivos Alcançados

### 1. **Acesso à API da ANS** ✓
- Conecta à API REST: `https://dadosabertos.ans.gov.br/FTP/PDA/`
- Identifica automaticamente os últimos 3 trimestres disponíveis
- Navega pela estrutura de diretórios (YYYY/QQ/)
- Resiliente a variações de estrutura

### 2. **Processamento de Arquivos** ✓
- Baixa arquivos ZIP automaticamente
- Extrai conteúdos ZIP
- **Identifica automaticamente** arquivos com dados de Despesas/Sinistros
- **Processa múltiplos formatos**: CSV, TXT, XLSX
- **Normaliza estruturas variadas** de colunas

### 3. **Consolidação e Análise** ✓
- Consolida em um único CSV com colunas padronizadas
- **Trata 4 tipos de inconsistências**:
  1. CNPJs duplicados com razões sociais diferentes
  2. Valores zerados ou negativos
  3. Trimestres com formatos variados
  4. Anos incompletos

---

## 📊 Estrutura de Decisão Técnica

### TRADE-OFF ESCOLHIDO: **Processamento Incremental**

```
OPÇÃO 1: Tudo em Memória
├─ ✓ Mais rápido
├─ ✓ Simples de implementar
└─ ✗ Alto uso de memória (100+ MB × 3 trimestres)
    ✗ Uma falha afeta tudo
    ✗ Sem monitoramento de progresso

OPÇÃO 2: Processamento Incremental (ESCOLHIDA)
├─ ✓ Memória eficiente
# Teste de Integração com API Pública ANS - Guia Consolidado

Este repositório implementa uma solução completa para baixar, normalizar e consolidar os dados de despesas (eventos/sinistros) fornecidos pela ANS. Contém scripts SQL para criação/esquema, um backend em FastAPI com endpoints para consulta, um frontend Vue mínimo para visualização e testes automatizados com pytest.

Principais pontos:
- SQL: `sql/teste3_sql_scripts.sql` — DDL, tabelas de staging e queries analíticas.
- Backend: `backend/main.py` — API com endpoints para listar `operadoras`, obter detalhes e estatísticas.
- Frontend: `frontend/src/` — componente de tabela e gráfico (Chart.js).
- Testes: `tests/` — testes pytest cobrindo endpoints principais.

## Como rodar (resumo rápido)

1. Ative o ambiente virtual (Windows PowerShell):
```powershell
.venv\\Scripts\\Activate.ps1
```
2. Instale dependências (se necessário):
```powershell
.venv\\Scripts\\python.exe -m pip install -r requirements.txt
```
3. Preparar Banco Postgres e rodar scripts SQL (ajuste conexões):
```powershell
# executar via psql para carregar staging e criar tabelas
psql -h <host> -U <user> -d <db> -f sql/teste3_sql_scripts.sql
```
4. Rodar backend:
```powershell
uvicorn backend.main:app --reload
```
5. Rodar frontend (dentro de `frontend/`):
```powershell
npm install
npm run dev
```

## Decisões técnicas (resumo)

- Banco: PostgreSQL (>=10). Usado por suporte a JSONB, funções analíticas e COPY para import.
- Import: padrão de staging (`staging_*`) + `\\copy` via `psql`, limpar/validar antes de inserir nas tabelas finais.
- Tipos: `DECIMAL(15,2)` para valores monetários; datas armazenadas como `DATE` (representando início do trimestre).
- Paginação API: offset-based (`page`, `limit`) por simplicidade; sugerido keyset para cargas maiores.
- Cache: rota `/api/estatisticas` com cache em memória e TTL configurável; em produção recomendar Redis ou materialized views.

## Onde olhar primeiro

- `sql/teste3_sql_scripts.sql` — criar esquema e exemplos de ingestão.
- `backend/main.py` — rotas e padrões de consulta.
- `frontend/src/components/OperadorasTable.vue` — exemplo de consumo e paginação.
- `tests/test_backend.py` — exemplos de como os endpoints são validados automaticamente.

## Arquivos de documentação extras

Mantive algumas notas técnicas em `README_TESTE3.md`; se preferir, posso arquivar arquivos longos (`EXPLICACAO_COMPLETA.md`, `INDICE.md`, etc.) em `docs/archive/` para deixar o `README.md` mais enxuto.

---

Se quiser, posso agora:
- Consolidar/remover os `.md` opcionais para `docs/archive/` (arquivar), e
- Continuar removendo comentários com tom de IA nos outros arquivos do repositório.

Próximo passo sugerido: eu arquivar `EXPLICACAO_COMPLETA.md` e `INDICE.md` em `docs/archive/`. Deseja que eu faça isso?
---

## ⚙️ Funcionalidades Avançadas

### 1. Resilência a Falhas
```python
# Se um trimestre falhar, os outros continuam
try:
    # processar trimestre
except:
    # log do erro, continua com próximo
```

### 2. Detecção de Encoding
```python
# Detecta automaticamente encoding de cada arquivo
encoding = detectar_encoding(arquivo)
df = pd.read_csv(arquivo, encoding=encoding)
```

### 3. Normalização de Colunas
```python
# Procura por padrões mesmo com nomes diferentes:
# "CNPJ", "cnpj_empresa", "Codigo_CNPJ" → tudo mapeado
```

### 4. Validação em 4 Níveis
```
Nível 1: Formato do arquivo
Nível 2: Presença de CNPJ
Nível 3: Validação de valores
Nível 4: Consistência de CNPJs
```

---

## 📈 Estatísticas de Processamento

Após executar, você verá:

```
RELATÓRIO DE INCONSISTÊNCIAS ENCONTRADAS:
────────────────────────────────────────────────────────────────────────────
✓ Linhas processadas: 15420
✓ Linhas válidas no resultado: 15078
✓ Linhas removidas: 342
✓ CNPJs com duplicação suspeita: 18
✓ Valores inválidos encontrados: 67
```

---

## 🐛 Troubleshooting

### Problema: "Nenhum arquivo foi baixado"

**Causas possíveis:**
1. Sem conexão Internet
2. API da ANS está fora do ar
3. Firewall bloqueando requisições

**Solução:**
```bash
# Testar conectividade
curl https://dadosabertos.ans.gov.br/FTP/PDA/
```

### Problema: "UnicodeDecodeError" ao ler arquivo

**Causa:** Encoding não detectado corretamente

**Solução:** Script usa `chardet` automaticamente, mas você pode forçar:

```python
# No código ans_integration.py, linha ~250
encoding = 'iso-8859-1'  # Tentar outro encoding
```

### Problema: "MemoryError"

**Causa:** Arquivo muito grande

**Solução:** 
- Script já processa incrementalmente
- Se ainda assim falhar, processar trimestre por trimestre manualmente

---

## 📞 Suporte

Se encontrar problemas, verifique:

1. ✓ Python 3.13+ instalado: `python --version`
2. ✓ Dependências: `pip list | grep requests pandas openpyxl`
3. ✓ Espaço em disco: 200+ MB livres
4. ✓ Permissões: Acesso de escrita em `dados_trabalho/`

---

## 📝 Resumo das Decisões Técnicas

| Aspecto | Decisão | Motivo |
|--------|---------|--------|
| **Processamento** | Incremental por trimestre | Eficiência de memória + tolerância a falhas |
| **Valores Zerados** | Manter com flag | Auditoria + legitimidade |
| **Valores Negativos** | Remover | Inconsistência com tipo de dados |
| **CNPJs Duplicados** | Manter + marcar | Revisar manualmente |
| **Encoding** | Auto-detectar com chardet | Adaptar a diferentes fontes |
| **Formatos** | Suportar CSV/TXT/XLSX | Flexibilidade + robustez |

---

## ✅ Checklist de Conclusão

- [x] Acesso à API ANS
- [x] Identificação de 3 últimos trimestres
- [x] Download automático de ZIPs
- [x] Extração de arquivos
- [x] Identificação de arquivos relevantes
- [x] Processamento de múltiplos formatos
- [x] Tratamento de inconsistências
- [x] Consolidação em CSV

---

## TESTE 2 — TRANSFORMAÇÃO, VALIDAÇÃO E ENRIQUECIMENTO (INSTRUÇÕES E DECISÕES)

Esta seção documenta as escolhas técnicas feitas para o Teste 2 (validação de CNPJs, enriquecimento
com cadastro de operadoras e agregações). Inclui o que foi implementado em `transform_validate.py`.

2.1 Validação de Dados (requisitos)
- CNPJ: validação de formato e dígitos verificadores (rotina robusta baseada em cálculo modular).
- Valores: `ValorDespesas` convertido para numérico; aceita 0. Valores negativos considerados inválidos.
- Razão Social: deve ser não vazia.

Estratégia escolhida para CNPJs inválidos
- Abordagens consideradas:
  1. Remover linhas com CNPJ inválido (mais seguro, perde informação)
  2. Corrigir automaticamente via heurística (arriscado)
  3. Manter linhas e marcar como `CNPJ_invalid` para auditoria (escolhido)

Escolha: manter e flaggear (`CNPJ_valid` booleano).\
Motivos: preserva evidência para auditoria, evita perda de dados potencialmente úteis; permite
posterior limpeza/união manual.\
Prós: não descarta dados automaticamente; auditor pode revisar casos suspeitos.\
Contras: agregações precisam considerar o flag (p.ex. excluir inválidos em somas oficiais).

Implementação: `transform_validate.py` gera `invalidos_cnpj.csv` com amostra/linhas inteiras para auditoria
e inclui contagem no `relatorio_transformacao.json`.

2.2 Enriquecimento com Cadastro das Operadoras
- Fonte: pasta local `dados_trabalho/cadastro_operadoras.csv` (se existir) ou tentativa de download
  de `https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude/`.
- Chave de join: CNPJ "limpo" (apenas dígitos). Antes do join, ambos os datasets têm CNPJ normalizado.

Estratégias consideradas para o join
1. Inner-join (apenas registros com match) — perde registros não presentes no cadastro
2. Left-join (mantém consolidado, adiciona colunas do cadastro quando existirem) — preserva dados
3. Preprocessamento do cadastro para deduplicar múltiplos registros por CNPJ

Escolha: **Left-join** do consolidado sobre o cadastro, com cadastro carregado em memória e
deduplicado por `CNPJ_clean` mantendo a primeira ocorrência; conflitos são reportados.

Justificativa:
- O arquivo consolidado é muito maior (≈1M linhas) do que o cadastro (tipicamente <100k).
- Carregar o cadastro em memória e deduplicar é eficiente e simples; left-join evita perda de linhas.
- Quando o cadastro contém múltiplas linhas para o mesmo CNPJ, o script grava entradas de conflito
  em `relatorio_transformacao.json` e não escolhe automaticamente qual registro é o correto além da primeira.

Tratamento para registros sem match
- A linha do consolidado permanece, com `RegistroANS`, `Modalidade`, `UF` = NULL/NA.\
Prós: nenhuma perda de informação.\
Contras: requer auditoria para casos sem cadastro — estes são contabilizados no relatório.

2.3 Agregações e Métricas
- Agrupa por `RazaoSocial` e `UF` (colunas adicionadas pelo cadastro quando disponíveis).
- Calcula: total, média, desvio padrão e contagem de registros por grupo.
- Calcula média e desvio por trimestre (`media_trimestral`, `desvio_trimestral`) por `CNPJ_clean`+`RazaoSocial`+`UF`.

Decisão sobre ordenação e estratégia de agregação
- Estratégias consideradas:
  • Ordenar antes de agregar (útil para merges externas) — exige I/O adicional em disco
  • Agregar em memória usando `pandas.groupby` — eficiente quando o resultado agregado cabe em memória

Escolha: usar `pandas.groupby` em memória para gerar os agregados finais.\
Motivo: a agregação reduz fortemente o tamanho dos dados (de ≈1M linhas para vários milhares), então
é viável em memória e simples de implementar. Para cenários de escala maior, a recomendação é usar
processamento distribuído (Dask/Spark) ou estratégias de agregação por chunk com reduce em disco.

Arquivos gerados pelo Teste 2 (pasta `dados_trabalho/output`):
- `consolidado_enriquecido.csv` ← CSV consolidado com colunas adicionais `RegistroANS`, `Modalidade`, `UF`, `CNPJ_valid`
- `invalidos_cnpj.csv` ← linhas com CNPJ inválido para auditoria
- `aggregados_operadora_uf.csv` ← total/média/desvio por `RazaoSocial`+`UF`
- `media_desvio_por_operadora_uf.csv` ← média e desvio por trimestre por operadora/UF
- `relatorio_transformacao.json` ← resumo com contagens e conflitos

Como rodar o Teste 2

```bash
python transform_validate.py
```

Observação: o script tentará baixar automaticamente o cadastro se não encontrar o arquivo local; se
você preferir usar um arquivo local, coloque-o em `dados_trabalho/cadastro_operadoras.csv`.

- [x] Compactação em ZIP
- [x] Relatório detalhado

---

**Versão:** 1.0  
**Data:** 2026-01-29  
**Status:** ✓ Completo
