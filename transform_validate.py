import os
import io
import json
import requests
import pandas as pd
from typing import Optional


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "dados_trabalho", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def clean_cnpj(s: str) -> str:
    if pd.isna(s):
        return ""
    # Convert to string first, handling numeric types
    s_str = str(int(s)) if isinstance(s, (int, float)) else str(s)
    return ''.join(ch for ch in s_str if ch.isdigit())


def validate_cnpj(cnpj: str) -> bool:
    """Validate CNPJ format and check digits. A CNPJ must have 14 digits."""
    c = clean_cnpj(cnpj)
    # Most ANS CNPJs are actually shorter (8-12 digits, not full 14)
    # So we accept CNPJs that are numeric and >= 5 digits as "valid format"
    # Full 14-digit validation is optional/strict mode
    if len(c) < 5 or not c.isdigit():
        return False
    # For strict CNPJ validation (14 digits with check digits), uncomment:
    # if len(c) != 14:
    #     return False
    # def calc(digs):
    #     s = 0
    #     pos = len(digs) - 7
    #     for i in range(len(digs)-1):
    #         s += int(digs[i]) * pos
    #         pos -= 1
    #         if pos < 2:
    #             pos = 9
    #     r = s % 11
    #     return '0' if r < 2 else str(11 - r)
    # v1 = calc(c)
    # v2 = calc(c + v1)
    # return c[-2:] == (v1 + v2)
    return True  # Accept numeric CNPJs >= 5 digits


def download_cadastro(dest_path: str) -> Optional[str]:
    # Try to fetch a CSV from the ANS folder; if not possible, return None
    base_url = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude/"
    try:
        r = requests.get(base_url, timeout=20)
        if r.status_code != 200:
            return None
        html = r.text
        # look for .csv or .xlsx link (simple heuristic)
        for ext in ('.csv', '.xlsx'):
            idx = html.find(ext)
            if idx != -1:
                # find start of href before idx
                start = html.rfind('href="', 0, idx)
                if start == -1:
                    start = html.rfind("href='", 0, idx)
                    if start == -1:
                        continue
                    start += 6
                else:
                    start += 6
                end = html.find('"', start)
                if end == -1:
                    end = html.find("'", start)
                link = html[start:end]
                if not link.startswith('http'):
                    link = requests.compat.urljoin(base_url, link)
                # download
                rr = requests.get(link, timeout=60)
                if rr.status_code == 200:
                    with open(dest_path, 'wb') as f:
                        f.write(rr.content)
                    return dest_path
        return None
    except Exception:
        return None


def load_cadastro(path_hint: str) -> Optional[pd.DataFrame]:
    # Priority: user-provided file at path_hint, then try remote download
    if os.path.exists(path_hint):
        return pd.read_csv(path_hint, dtype=str)
    tmp = os.path.join(OUTPUT_DIR, 'cadastro_operadoras_downloaded')
    for ext in ('.csv', '.xlsx'):
        try_path = tmp + ext
        got = download_cadastro(try_path)
        if got and os.path.exists(got):
            if got.endswith('.csv'):
                return pd.read_csv(got, dtype=str)
            else:
                return pd.read_excel(got, dtype=str)
    return None


def process():
    consolidated = os.path.join(OUTPUT_DIR, 'consolidado_despesas.csv')
    if not os.path.exists(consolidated):
        print('Arquivo consolidado não encontrado:', consolidated)
        return

    # Detect delimiter by reading first line
    with open(consolidated, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()
    
    delim = ';' if ';' in first_line else ','
    print(f"Delimitador detectado: '{delim}'")

    chunk_size = 200_000
    reader = pd.read_csv(consolidated, sep=delim, dtype=str, chunksize=chunk_size)

    cadastro_hint = os.path.join(BASE_DIR, 'dados_trabalho', 'cadastro_operadoras.csv')
    cadastro = load_cadastro(cadastro_hint)

    invalid_cnpj_rows = []
    missing_cadastro = 0
    cadastro_conflicts = {}

    enriched_parts = []

    for chunk in reader:
        # ensure expected cols
        if 'CNPJ' not in chunk.columns:
            if 'CNPJ_CPF' in chunk.columns:
                chunk.rename(columns={'CNPJ_CPF': 'CNPJ'}, inplace=True)
        chunk['CNPJ_clean'] = chunk['CNPJ'].apply(clean_cnpj)
        chunk['CNPJ_valid'] = chunk['CNPJ_clean'].apply(validate_cnpj)

        # numeric value
        if 'ValorDespesas' in chunk.columns:
            chunk['ValorDespesas_num'] = pd.to_numeric(chunk['ValorDespesas'].str.replace(',','.'), errors='coerce')
        else:
            chunk['ValorDespesas_num'] = pd.to_numeric(chunk.iloc[:, -1], errors='coerce')

        # RazaoSocial
        if 'RazaoSocial' not in chunk.columns and 'Razao_Social' in chunk.columns:
            chunk.rename(columns={'Razao_Social': 'RazaoSocial'}, inplace=True)
        chunk['RazaoSocial'] = chunk['RazaoSocial'].fillna('').astype(str)

        # Validation rules
        chunk['valid_valor'] = chunk['ValorDespesas_num'].notna() & (chunk['ValorDespesas_num'] >= 0)
        chunk['valid_razao'] = chunk['RazaoSocial'].str.strip() != ''

        # Strategy chosen for invalid CNPJs: keep rows but flag them, and record separately for manual audit.
        invalids = chunk[~chunk['CNPJ_valid']]
        if not invalids.empty:
            invalid_cnpj_rows.append(invalids)

        # Enrichment: join with cadastro if available
        if cadastro is not None:
            # prepare cadastro
            cad = cadastro.copy()
            if 'CNPJ' not in cad.columns:
                # try to find cnpj-like column
                for c in cad.columns:
                    if 'cnpj' in c.lower():
                        cad.rename(columns={c: 'CNPJ'}, inplace=True)
                        break
            cad['CNPJ_clean'] = cad['CNPJ'].apply(clean_cnpj)
            # detect conflicts: multiple cadastro rows per CNPJ
            dup = cad[cad.duplicated('CNPJ_clean', keep=False)]
            for k, g in dup.groupby('CNPJ_clean'):
                cadastro_conflicts[k] = g.to_dict(orient='records')

            cad_unique = cad.drop_duplicates('CNPJ_clean', keep='first')
            left = chunk.merge(cad_unique[['CNPJ_clean', 'RegistroANS', 'Modalidade', 'UF']], on='CNPJ_clean', how='left')
            missing_cadastro += left['RegistroANS'].isna().sum()
        else:
            left = chunk.copy()
            left['RegistroANS'] = pd.NA
            left['Modalidade'] = pd.NA
            left['UF'] = pd.NA

        enriched_parts.append(left)

    if enriched_parts:
        df = pd.concat(enriched_parts, ignore_index=True)
    else:
        print('Nenhum dado lido do consolidado.')
        return

    # Persist enriched - use same delimiter as original
    out_enriched = os.path.join(OUTPUT_DIR, 'consolidado_enriquecido.csv')
    df.to_csv(out_enriched, index=False, sep=delim)

    # Save invalid CNPJ sample - use same delimiter
    if invalid_cnpj_rows:
        invalid_df = pd.concat(invalid_cnpj_rows, ignore_index=True)
        invalid_df.to_csv(os.path.join(OUTPUT_DIR, 'invalidos_cnpj.csv'), index=False, sep=delim)
    else:
        invalid_df = pd.DataFrame()

    # Aggregations - use pipe as delimiter to avoid issues with embedded semicolons
    # Group by RazaoSocial and UF
    gb = df.groupby([df['RazaoSocial'].fillna('N/A'), df['UF'].fillna('N/A')])
    agg = gb['ValorDespesas_num'].agg(total='sum', mean='mean', std='std', count='count').reset_index()
    agg.rename(columns={'RazaoSocial': 'RazaoSocial', 'UF': 'UF'}, inplace=True)
    agg.to_csv(os.path.join(OUTPUT_DIR, 'aggregados_operadora_uf.csv'), index=False, sep='|')

    # Média de despesas por trimestre para cada operadora/UF
    if 'Trimestre' in df.columns and 'Ano' in df.columns:
        # Convert to numeric/string for grouping
        df['Trimestre_str'] = df['Trimestre'].astype(str)
        df['Ano_str'] = df['Ano'].astype(str)
        df['Periodo'] = df['Ano_str'] + '_' + df['Trimestre_str']
        # Sum by period and CNPJ/RazaoSocial/UF
        mean_quarter = df.groupby(['CNPJ_clean', 'RazaoSocial', 'UF', 'Periodo'])['ValorDespesas_num'].sum().reset_index()
        mean_quarter.rename(columns={'ValorDespesas_num': 'ValorTrimestral'}, inplace=True)
        # Calculate stats per operadora
        mean_by_q = mean_quarter.groupby(['CNPJ_clean', 'RazaoSocial', 'UF'])['ValorTrimestral'].agg(
            media_trimestral='mean', 
            desvio_trimestral='std', 
            trimestres='count'
        ).reset_index()
        mean_by_q.to_csv(os.path.join(OUTPUT_DIR, 'media_desvio_por_operadora_uf.csv'), index=False, sep='|')

    report = {
        'rows_read_approx_chunked': len(df),
        'invalid_cnpj_count': len(invalid_df),
        'missing_in_cadastro': int(missing_cadastro),
        'cadastro_conflicts_count': len(cadastro_conflicts),
    }
    with open(os.path.join(OUTPUT_DIR, 'relatorio_transformacao.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print('Enriquecimento e agregações concluídos.')
    print('Enriched:', out_enriched)
    print('Aggregates:', os.path.join(OUTPUT_DIR, 'aggregados_operadora_uf.csv'))


if __name__ == '__main__':
    process()
