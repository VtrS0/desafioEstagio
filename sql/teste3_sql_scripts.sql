
-- SQL scripts for Teste 3 (PostgreSQL >= 10)
-- DDL, import examples and analytical queries

-- ===== DDL: operadoras (cadastro) =====
CREATE TABLE IF NOT EXISTS operadoras (
  cnpj VARCHAR(20) PRIMARY KEY,
  razao_social TEXT NOT NULL,
  nome_fantasia TEXT,
  tipo_operadora TEXT,
  endereco TEXT,
  uf VARCHAR(2),
  cidade TEXT,
  inscricao_estadual TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_operadoras_uf ON operadoras(uf);

-- ===== DDL: consolidado_despesas =====
-- stores per-operadora per-quarter expense records
CREATE TABLE IF NOT EXISTS consolidado_despesas (
  id BIGSERIAL PRIMARY KEY,
  cnpj VARCHAR(20) NOT NULL REFERENCES operadoras(cnpj),
  uf VARCHAR(2) NOT NULL,
  trimestre_date DATE NOT NULL, -- store as date (quarter start, e.g., '2025-01-01')
  despesa_total DECIMAL(15,2) NOT NULL,
  detalhe JSONB, -- optional extra details
  inserted_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_consolidado_cnpj_trimestre ON consolidado_despesas(cnpj, trimestre_date);
CREATE INDEX IF NOT EXISTS idx_consolidado_uf ON consolidado_despesas(uf);

-- ===== DDL: despesas_agregadas =====
CREATE TABLE IF NOT EXISTS despesas_agregadas (
  id BIGSERIAL PRIMARY KEY,
  uf VARCHAR(2),
  operadora_cnpj VARCHAR(20),
  trimestre_date DATE,
  despesa DECIMAL(15,2),
  metric_source TEXT,
  inserted_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_agregadas_uf ON despesas_agregadas(uf);
CREATE INDEX IF NOT EXISTS idx_agregadas_operadora_trimestre ON despesas_agregadas(operadora_cnpj, trimestre_date);

-- ===== Import pattern (recommended) =====
-- Use a staging table to import raw CSV and then transform/validate into normalized tables.

-- 1) Create staging table matching CSV structure (example for consolidado_despesas.csv)
CREATE TABLE IF NOT EXISTS staging_consolidado_raw (
  raw_line TEXT,
  cnpj TEXT,
  uf TEXT,
  trimestre TEXT,
  despesa TEXT
);

-- 2) Import CSV using psql client command (this respects client encoding):
-- psql -h <host> -U <user> -d <db> -c "\copy staging_consolidado_raw(cnpj,uf,trimestre,despesa) FROM 'consolidado_despesas.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')"

-- 3) Clean and insert into final table with conversions and basic validations
-- Sample insert with robust parsing (handles commas/dots in numbers and some date formats)
INSERT INTO consolidado_despesas(cnpj, uf, trimestre_date, despesa_total, detalhe)
SELECT
  trim(NULLIF(cnpj, '')) AS cnpj_clean,
  upper(trim(NULLIF(uf, ''))) AS uf_clean,
  -- convert trimestre to a quarter start date: try YYYY-MM-DD, else try YYYY-Qn, else parse first 4 chars as year
  (CASE
     WHEN trimestre ~ '^\\d{4}-\\d{2}-\\d{2}$' THEN cast(trimestre AS DATE)
     WHEN trimestre ~ '^\\d{4}-Q[1-4]$' THEN
       to_date(substring(trimestre from 1 for 4) || '-' ||
         CASE substring(trimestre from 6 for 1) WHEN '1' THEN '01-01' WHEN '2' THEN '04-01' WHEN '3' THEN '07-01' ELSE '10-01' END, 'YYYY-MM-DD')
     ELSE to_date(substring(trimestre from 1 for 4) || '-01-01', 'YYYY-MM-DD')
   END) as trimestre_date_clean,
  -- numeric cleaning: remove dots used as thousand separators and replace comma decimal separator
  (CASE
    WHEN regexp_replace(despesa, '[^0-9,.-]', '', 'g') ~ '^[0-9]+([.,][0-9]+)?$' THEN
      cast(replace(replace(regexp_replace(despesa, '[^0-9,.-]', '', 'g'), '.', ''), ',', '.') AS NUMERIC)
    ELSE NULL
   END) as despesa_clean,
  jsonb_build_object('src_row', ctid)::jsonb
FROM staging_consolidado_raw
WHERE trim(NULLIF(cnpj, '')) IS NOT NULL
  AND trim(NULLIF(uf, '')) <> ''
  AND (regexp_replace(despesa, '[^0-9,.-]', '', 'g') ~ '^[0-9]+([.,][0-9]+)?$');

-- Note: Rows with invalid numeric values or missing mandatory fields are excluded by WHERE clause.
-- You can instead INSERT into an errors table for manual review.

-- ===== IMPORT using COPY for despesas_agregadas.csv and operadoras CSV =====
-- Create staging table for operadoras raw
CREATE TABLE IF NOT EXISTS staging_operadoras_raw (
  cnpj TEXT,
  razao_social TEXT,
  nome_fantasia TEXT,
  tipo_operadora TEXT,
  endereco TEXT,
  uf TEXT,
  cidade TEXT
);
-- psql \copy staging_operadoras_raw FROM 'operadoras.csv' CSV HEADER ENCODING 'UTF8'

-- Insert into operadoras with basic validation
INSERT INTO operadoras(cnpj, razao_social, nome_fantasia, tipo_operadora, endereco, uf, cidade)
SELECT
  regexp_replace(trim(cnpj), '[^0-9]', '', 'g') as cnpj_only_digits,
  trim(NULLIF(razao_social, '')),
  trim(NULLIF(nome_fantasia, '')),
  trim(NULLIF(tipo_operadora, '')),
  trim(NULLIF(endereco, '')),
  upper(trim(NULLIF(uf, ''))),
  trim(NULLIF(cidade, ''))
FROM staging_operadoras_raw
WHERE trim(NULLIF(cnpj, '')) IS NOT NULL AND trim(NULLIF(razao_social, '')) IS NOT NULL;

-- For despesas_agregadas, follow similar staging + insert pattern shown above.

-- ===== ANALYTICAL QUERIES =====
-- Query 1: Top 5 operadoras with largest percentual growth between first and last quarter in dataset
-- Approach: Use quarter min/max across dataset; require that operadora has non-null values in both quarters to avoid division by zero or misleading growth from missing.

-- Identify dataset first and last quarter
WITH quarters AS (
  SELECT min(trimestre_date) as first_q, max(trimestre_date) as last_q FROM consolidado_despesas
), sums AS (
  SELECT cnpj, trimestre_date, SUM(despesa_total) as total_q
  FROM consolidado_despesas
  GROUP BY cnpj, trimestre_date
), pivot AS (
  SELECT s.cnpj,
    (SELECT total_q FROM sums WHERE sums.cnpj = s.cnpj AND sums.trimestre_date = (SELECT first_q FROM quarters)) as v_first,
    (SELECT total_q FROM sums WHERE sums.cnpj = s.cnpj AND sums.trimestre_date = (SELECT last_q FROM quarters)) as v_last
  FROM (SELECT DISTINCT cnpj FROM consolidado_despesas) s
)
SELECT cnpj, v_first, v_last,
  CASE WHEN v_first IS NULL OR v_first = 0 THEN NULL ELSE ROUND( (v_last - v_first) / v_first * 100.0, 4) END as pct_growth
FROM pivot
WHERE v_first IS NOT NULL AND v_last IS NOT NULL
ORDER BY pct_growth DESC NULLS LAST
LIMIT 5;

-- Note: We require both quarters present. Alternative: treat missing as 0 (inflates growth) — documented choice in README.

-- Query 2: Distribution of despesas by UF and top 5 states, plus mean per operadora in each UF
-- Total per UF
SELECT uf, SUM(despesa_total) as total_despesas
FROM consolidado_despesas
GROUP BY uf
ORDER BY total_despesas DESC
LIMIT 5;

-- Mean per operadora in each UF
SELECT uf, AVG(sum_per_operadora) as media_por_operadora
FROM (
  SELECT uf, cnpj, SUM(despesa_total) as sum_per_operadora
  FROM consolidado_despesas
  GROUP BY uf, cnpj
) t
GROUP BY uf
ORDER BY media_por_operadora DESC
LIMIT 10;

-- Query 3: How many operadoras had despesas above overall mean in at least 2 of the 3 trimestres
-- Approach: compute mean per quarter across operadoras, then count quarters per operadora where their quarter total > quarter mean, finally count operadoras with count >= 2.
WITH quarter_stats AS (
  SELECT trimestre_date, AVG(total_q) as quarter_mean
  FROM (
    SELECT trimestre_date, cnpj, SUM(despesa_total) as total_q
    FROM consolidado_despesas
    GROUP BY trimestre_date, cnpj
  ) s
  GROUP BY trimestre_date
), per_operadora_quarter AS (
  SELECT s.cnpj, s.trimestre_date, SUM(s.despesa_total) as total_q
  FROM consolidado_despesas s
  GROUP BY s.cnpj, s.trimestre_date
), flagged AS (
  SELECT p.cnpj, p.trimestre_date,
    p.total_q, q.quarter_mean,
    CASE WHEN p.total_q > q.quarter_mean THEN 1 ELSE 0 END as above_mean
  FROM per_operadora_quarter p
  JOIN quarter_stats q USING (trimestre_date)
)
SELECT COUNT(DISTINCT cnpj) as operadoras_count
FROM (
  SELECT cnpj, SUM(above_mean) as quarters_above
  FROM flagged
  GROUP BY cnpj
  HAVING SUM(above_mean) >= 2
) t;

-- End of file
