# GUIA DE USO - ARQUIVO CONSOLIDADO DE DESPESAS ANS

## 📦 O QUE VOCÊ RECEBEU

Sua pasta contém:

```
c:\Users\AMD\Documents\desafioEstagio\dados_trabalho\output\

├── consolidado_despesas.zip          ← ARQUIVO PRINCIPAL (6.4 MB)
│   └─ consolidado_despesas.csv       (dentro do ZIP)
│   └─ relatorio_inconsistencias.json (dentro do ZIP)
│
├── consolidado_despesas.csv          (64.8 MB - versão solta)
└── relatorio_inconsistencias.json    (92.4 MB - detalhes de inconsistências)
```

---

## 🎯 COMO USAR

### Opção 1: Usar o ZIP (Recomendado)
```
1. Fazer download de: consolidado_despesas.zip
2. Descompactar em sua máquina
3. Abrir consolidado_despesas.csv em:
   - Excel
   - Google Sheets
   - Python/Pandas
   - SQL
```

### Opção 2: Usar o CSV Diretamente
```
1. Fazer download de: consolidado_despesas.csv
2. Abrir em seu aplicativo favorito
3. Filtrar e analisar
```

---

## 📊 CONTEÚDO DO CSV

### Colunas
```
CNPJ              Código da operadora (ex: 344800)
RazaoSocial       Nome da operadora/descrição
Trimestre         Período (01, 02, 03, 04)
Ano               Ano (2025)
ValorDespesas     Valor em reais (R$)
status            OK ou ZERADO
```

### Exemplo de Dados
```
CNPJ,RazaoSocial,Trimestre,Ano,ValorDespesas,status
344800,Contribuição Social a Compensar/Restituir,01,2025,0.0,ZERADO
344800,Outros Ativos Intangíveis,01,2025,0.0,ZERADO
344800,Despesas com Encargos Sociais,01,2025,45000.50,OK
```

---

## 🔍 ENTENDENDO AS INCONSISTÊNCIAS

### "Status: ZERADO" significa:
```
✓ Valor = R$ 0.00
✓ Registrado como válido (pode ser legítimo)
✓ Operadora SEM despesas naquele trimestre
✓ MANTIDO para rastreabilidade completa
```

### "Status: OK" significa:
```
✓ Valor > R$ 0.00
✓ Registro ativo
✓ Operadora COM despesas no trimestre
```

### Registros REMOVIDOS (não aparecem no CSV)
```
✗ Valor < R$ 0.00 (negativo)
  → São créditos/devoluções, não despesas
  → Removidos por serem inconsistentes com tipo de dados

✗ CNPJ vazio
  → Impossível identificar operadora
  → Removidos por falta de chave primária
```

---

## ⚠️ AVISO IMPORTANTE: CNPJs Duplicados

### PROBLEMA DETECTADO
```
808 CNPJs aparecem com 2 ou mais razões sociais diferentes
Exemplo: CNPJ 344800 tem 808+ razões sociais!
```

### O que significa?
```
Opção 1: Fusão/incorporação de empresas
Opção 2: Renomeação da operadora
Opção 3: Erro de consolidação nos dados originais da ANS
```

### Recomendação
```
⚠️ REVISAR EM AUDITORIA
Validar contra base oficial da ANS
Confirmar registro em CNAE/CNPJ
```

---

## 📈 COMO ANALISAR OS DADOS

### Excel - Filtros Rápidos
```
1. Abrir consolidado_despesas.csv
2. Selecionar cabeçalho
3. Dados → Filtro Automático
4. Filtrar por:
   - Trimestre (01, 02, 03)
   - Ano (2025)
   - Status (OK, ZERADO)
   - Faixa de Valores
```

### Python - Análise Rápida
```python
import pandas as pd

# Carregar
df = pd.read_csv('consolidado_despesas.csv')

# Top 10 operadoras por valor
df.groupby('RazaoSocial')['ValorDespesas'].sum().sort_values(ascending=False).head(10)

# Por trimestre
df.groupby('Trimestre')['ValorDespesas'].sum()

# Valores zerados vs OK
df['status'].value_counts()
```

### SQL - Importar
```sql
-- Criar tabela
CREATE TABLE despesas_ans (
    cnpj VARCHAR(20),
    razao_social VARCHAR(255),
    trimestre VARCHAR(2),
    ano INT,
    valor_despesas DECIMAL(15,2),
    status VARCHAR(10)
);

-- Importar CSV
LOAD DATA INFILE 'consolidado_despesas.csv'
INTO TABLE despesas_ans
FIELDS TERMINATED BY ','
IGNORE 1 ROWS;
```

---

## 📋 RELATÓRIO DE INCONSISTÊNCIAS

Arquivo: `relatorio_inconsistencias.json`

```json
{
  "linhas_processadas": 2113924,
  "linhas_removidas": 1087121,
  "linhas_finais": 1026803,
  "cnpj_duplicados_suspeitos": 808,
  "valores_invalidos": 983212,
  "taxa_aceitacao": "48.6%"
}
```

### Interpretação
```
Total de linhas lidas:        2.113.924
Linhas removidas por erro:    1.087.121 (51.4%)
Linhas válidas no resultado:  1.026.803 (48.6%)

CNPJs problemáticos:          808
Valores zerados encontrados:  983.212
```

---

## 🔐 SEGURANÇA E CONFORMIDADE

### Dados Incluídos
```
✓ CNPJ (código único)
✓ Razão Social (nome)
✓ Período (trimestre/ano)
✓ Valor (despesa)
```

### Dados NÃO Incluídos
```
✗ Dados pessoais de beneficiários
✗ Informações de pacientes
✗ Detalhes de sinistros individuais
✗ Dados sensíveis
```

### Classificação
```
Nível de Sigilo: PÚBLICO
Fonte: ANS (Agência Nacional de Saúde Suplementar)
Disponibilidade: Open Data
```

---

## 🆘 DÚVIDAS FREQUENTES

### P: Por que tem tantos valores zerados?
```
R: Pode indicar:
   ✓ Trimestre ainda não fechado
   ✓ Operadora sem atividade no período
   ✓ Dados ainda não consolidados na ANS
```

### P: Como trato os CNPJs duplicados?
```
R: Opções:
   1. Agrupar por CNPJ (soma valores)
   2. Manter separados por razão social
   3. Investigar qual é a correta
   4. Contatar ANS para confirmação
```

### P: Posso comparar trimestres?
```
R: Sim! Filtre por:
   - Mesmo CNPJ
   - Diferentes trimestres
   - Compare ValorDespesas
```

### P: Por que algumas linhas foram removidas?
```
R: Três motivos:
   1. Valor negativo (R$ < 0) → Crédito, não despesa
   2. CNPJ vazio → Sem identificação
   3. Trimestre/Ano incompleto → Dados inválidos
```

---

## 📞 CONTATO PARA DÚVIDAS

```
Dados Originais: ANS (Agência Nacional de Saúde Suplementar)
Portal: https://dadosabertos.ans.gov.br/

Processamento: Script Python (ans_integration.py)
Documentação: Veja README.md e RESUMO_EXECUCAO.md
```

---

## ✅ PRÓXIMOS PASSOS RECOMENDADOS

1. **Validação**
   - Verificar amostra de 100 registros
   - Confirmar totais por trimestre
   - Cruzar com dados originais

2. **Análise**
   - Exportar para BI (Power BI, Tableau)
   - Gerar gráficos por operadora
   - Identificar tendências

3. **Integração**
   - Importar em banco de dados
   - Automatizar atualização mensal
   - Criar dashboards

4. **Auditoria**
   - Revisar 808 CNPJs duplicados
   - Validar amostra aleatória
   - Confirmar taxa de rejeição

---

## 📅 VERSIONAMENTO

```
Dataset Version: 1.0
Trimestres: 1T2025, 2T2025, 3T2025
Data de Processamento: 2026-01-29
Formato: CSV UTF-8
Compressão: ZIP Deflate
Encoding: Automático detectado
```

---

**Arquivo Gerado Automaticamente pelo Sistema de Integração ANS**  
**Uso: Análise, Auditoria e Business Intelligence**
