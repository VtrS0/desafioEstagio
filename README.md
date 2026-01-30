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
├─ ✓ Falha isolada por trimestre
├─ ✓ Monitoramento de progresso
├─ ✓ Escalável para volumes maiores
└─ Apenas 2-3% mais lento
```

**Justificativa:**
- Volumes de dados da ANS podem exceder 100MB
- Melhor tratamento de erros (falha isolada)
- Permite recuperação e retentativa
- Essencial para ambientes com recursos limitados

---

## 🔍 Tratamento de Inconsistências

### 1️⃣ **CNPJs Duplicados com Razões Sociais Diferentes**
```
Situação: CNPJ 12.345.678/0001-90
          - Razão Social A
          - Razão Social B

Ação: MANTÉM ambos, marca com flag "DUPLICADO_SUSPEITO"
Motivo: Pode indicar:
  • Fusão/incorporação
  • Renomeação da empresa
  • Erro de lançamento
  
Recomendação: Revisar manualmente
```

### 2️⃣ **Valores Zerados**
```
Situação: Linha com valor = 0

Ação: MANTÉM a linha com status='ZERADO'
Motivo: 
  • Pode ser legítimo (sem despesas no trimestre)
  • Importante para auditoria
  
Resultado: Não distorce totalizações
```

### 3️⃣ **Valores Negativos**
```
Situação: Linha com valor < 0

Ação: REMOVE a linha
Motivo:
  • Deveriam ser créditos/devoluções (outras tabelas)
  • Inversão de sinal indicaria erro
  
Log: Registrado em relatorio_inconsistencias.json
```

### 4️⃣ **Formatos de Data/Trimestre**
```
Conversões Automáticas:
  • Q1, Q2, Q3, Q4 → 01, 02, 03, 04
  • 1, 2, 3, 4 → 01, 02, 03, 04
  • Ano "24" → "2024"
  • Ano "2024" → "2024" (mantém)
```

---

## 📁 Estrutura de Arquivos

```
desafioEstagio/
│
├── ans_integration.py          # Script principal
├── README.md                   # Este arquivo
│
└── dados_trabalho/             # Criado automaticamente
    ├── downloads/              # Arquivos ZIP baixados
    │   ├── 2024_03_file1.zip
    │   ├── 2024_02_file2.zip
    │   └── 2024_01_file3.zip
    │
    ├── extraido/               # Arquivos extraídos
    │   ├── Despesas_2024_Q3.csv
    │   ├── Sinistros_2024_Q2.xlsx
    │   └── ...
    │
    └── output/                 # Resultados finais ⭐
        ├── consolidado_despesas.csv        # CSV final
        ├── relatorio_inconsistencias.json  # Detalhes
        └── consolidado_despesas.zip        # Arquivo entregável
```

---

## 🚀 Como Usar

### Pré-requisitos
- Python 3.13+
- Conexão com Internet
- 200 MB de espaço livre (aproximado)

### Passo 1: Executar o Script

```bash
python ans_integration.py
```

### Passo 2: Saída Esperada

```
╔════════════════════════════════════════════════════════════════════════════╗
║          TESTE DE INTEGRAÇÃO COM API PÚBLICA ANS                          ║
║     Consolidação de Despesas com Eventos/Sinistros - Últimos 3 Trimestres ║
╚════════════════════════════════════════════════════════════════════════════╝

================================================================================
PASSO 1: DESCOBRINDO TRIMESTRES DISPONÍVEIS NA API ANS
================================================================================

✓ Conexão com API estabelecida: https://dadosabertos.ans.gov.br/FTP/PDA/
✓ Status: 200
✓ Anos encontrados: ['2024', '2023']
✓ Explorando trimestres disponíveis...
  → 2024/03/
  → 2024/02/
  → 2024/01/

✓ Selecionados 3 trimestres para processamento:
  → 2024/Q03
  → 2024/Q02
  → 2024/Q01

[... passo 2, 3, 4, 5, 6 ...]

✓ PROCESSO FINALIZADO COM SUCESSO!
================================================================================
```

### Passo 3: Localizar Resultado

```
📦 Localização: c:\Users\AMD\Documents\desafioEstagio\dados_trabalho\output\

Arquivos gerados:
  ✓ consolidado_despesas.zip ← ARQUIVO PRINCIPAL
  ✓ consolidado_despesas.csv ← Dados processados
  ✓ relatorio_inconsistencias.json ← Relatório técnico
```

---

## 📋 Formato do CSV de Saída

### Colunas
```
CNPJ              | RazaoSocial        | Trimestre | Ano  | ValorDespesas | Status
12.345.678/001-90 | Empresa XYZ Ltda   | 03        | 2024 | 150000.00     | OK
98.765.432/001-10 | Operadora ABC      | 03        | 2024 | 0.00          | ZERADO
...
```

### Exemplo de Dados
```csv
CNPJ,RazaoSocial,Trimestre,Ano,ValorDespesas,Status
12.345.678/0001-90,OPERADORA A,01,2024,1500000.50,OK
12.345.678/0001-90,OPERADORA A,02,2024,1600000.75,OK
98.765.432/0001-10,OPERADORA B,01,2024,0.00,ZERADO
98.765.432/0001-10,OPERADORA B,02,2024,800000.00,OK
```

---

## 📊 Relatório de Inconsistências

Arquivo `relatorio_inconsistencias.json` contém:

```json
{
  "cnpj_duplicados_suspeitos": [
    {
      "cnpj": "12.345.678/0001-90",
      "razoes_sociais": ["OPERADORA A", "OPERADORA ALPHA"]
    }
  ],
  "valores_invalidos": [
    {
      "cnpj": "11.111.111/0001-11",
      "tipo": "NEGATIVO",
      "valor": -5000.00
    },
    {
      "cnpj": "22.222.222/0001-22",
      "tipo": "ZERADO",
      "valor": 0.00
    }
  ],
  "linhas_processadas": 15420,
  "linhas_removidas": 342,
  "linhas_finais": 15078
}
```

---

## 🔧 Detalhes Técnicos

### Dependências Instaladas
```
requests       → Acesso HTTP à API
pandas         → Processamento de dados
openpyxl       → Leitura de arquivos Excel
chardet        → Detecção automática de encoding
```

### Identificação Automática de Arquivos Relevantes

O script busca por palavras-chave nos nomes de arquivos:
```python
['despesa', 'sinistro', 'evento', 'claim', 'expense', 
 'beneficiario', 'participante', 'custeio']
```

Se não encontrar, extrai todos os arquivos `.csv`, `.txt`, `.xlsx`

### Detecção Automática de Encoding

Utiliza `chardet` para detectar automaticamente:
- UTF-8
- ISO-8859-1 (Latin-1)
- CP1252 (Windows-1252)
- Outros codificadores

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
