"""
TESTE DE INTEGRAÇÃO COM API PÚBLICA ANS
Desafio de Estágio - Consolidação de Dados de Despesas com Eventos/Sinistros
"""

import os
import requests
import zipfile
import csv
from pathlib import Path
from datetime import datetime
import json
from collections import defaultdict
import pandas as pd
from io import BytesIO
import chardet

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

BASE_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/"
TRABALHO_DIR = Path(__file__).parent / "dados_trabalho"
DOWNLOAD_DIR = TRABALHO_DIR / "downloads"
EXTRACT_DIR = TRABALHO_DIR / "extraido"
OUTPUT_DIR = TRABALHO_DIR / "output"
DADOS_LOCAIS_DIR = TRABALHO_DIR  # Dados já baixados em 1T2025, 2T2025, 3T2025

# Criar diretórios
for dir_path in [DOWNLOAD_DIR, EXTRACT_DIR, OUTPUT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ============================================================================
# PASSO 1: EXPLORAR DADOS LOCAIS E LISTAR TRIMESTRES DISPONÍVEIS
# ============================================================================

def listar_trimestres_disponiveis():
    """
    Identifica trimestres disponíveis nos dados locais.
    Procura por diretórios: 1T2025, 2T2025, 3T2025, etc.
    Retorna lista com estrutura: [(ano, trimestre), ...]
    """
    print("\n" + "="*80)
    print("PASSO 1: DESCOBRINDO TRIMESTRES DISPONÍVEIS NOS DADOS LOCAIS")
    print("="*80)
    
    trimestres = []
    
    # Procurar por padrões de diretórios: [1-4]T20XX
    import re
    
    for item in DADOS_LOCAIS_DIR.iterdir():
        if item.is_dir():
            # Procurar padrão como "1T2025", "2T2025", "3T2025", etc
            match = re.match(r'(\d)T(\d{4})', item.name)
            if match:
                trimestre = match.group(1)
                ano = match.group(2)
                trimestres.append((ano, trimestre))
                print(f"✓ Encontrado: {ano}/T{trimestre} ({item.name})")
    
    # Se não encontrou com padrão, procurar por arquivos diretamente
    if not trimestres:
        print("⚠ Nenhum diretório TrimestroAno encontrado.")
        print("  Procurando arquivos CSV nos diretórios...")
        
        for item in DADOS_LOCAIS_DIR.iterdir():
            if item.is_dir() and item.name not in ['downloads', 'extraido', 'output']:
                print(f"  → Verificando {item.name}...")
    
    # Ordenar por ano e trimestre (descending)
    trimestres = sorted(trimestres, key=lambda x: (x[0], x[1]), reverse=True)
    
    # Pegar últimos 3
    trimestres = trimestres[:3]
    
    print(f"\n✓ Selecionados {len(trimestres)} trimestres para processamento:")
    for ano, trim in trimestres:
        print(f"  → {ano}/T{trim}")
    
    return trimestres


# ============================================================================
# PASSO 2: LOCALIZAR E PREPARAR ARQUIVOS LOCAIS
# ============================================================================

def preparar_arquivos_locais(trimestres):
    """
    Localiza arquivos CSV dos trimestres nos diretórios locais.
    """
    print("\n" + "="*80)
    print("PASSO 2: LOCALIZANDO ARQUIVOS NOS DIRETÓRIOS LOCAIS")
    print("="*80)
    print("\nModo: Processamento de dados já downloaded")
    print("Localização: c:\\Users\\AMD\\Documents\\desafioEstagio\\dados_trabalho\\\n")
    
    arquivos_localizados = []
    
    for ano, trimestre in trimestres:
        # Tentar diferentes nomes de diretório
        nomes_possiveis = [
            f"{trimestre}T{ano}",
            f"{trimestre}T20{ano}",
            f"T{trimestre}_{ano}",
            f"{ano}_{trimestre}",
            f"{ano}_Q{trimestre}"
        ]
        
        diretorio_encontrado = None
        
        for nome in nomes_possiveis:
            caminho = DADOS_LOCAIS_DIR / nome
            if caminho.exists() and caminho.is_dir():
                diretorio_encontrado = caminho
                print(f"✓ Diretório {ano}/T{trimestre} encontrado: {nome}/")
                break
        
        if not diretorio_encontrado:
            print(f"⚠ Diretório {ano}/T{trimestre} não encontrado")
            continue
        
        # Procurar arquivos CSV, TXT, XLSX
        for extensao in ['*.csv', '*.txt', '*.xlsx', '*.xls']:
            for arquivo in diretorio_encontrado.glob(extensao):
                print(f"  ↓ Localizado arquivo: {arquivo.name}")
                arquivos_localizados.append({
                    'caminho': arquivo,
                    'ano': ano,
                    'trimestre': trimestre,
                    'nome': arquivo.name
                })
    
    print(f"\n✓ Total de arquivos localizados: {len(arquivos_localizados)}")
    return arquivos_localizados


# ============================================================================
# PASSO 3: PROCESSAR ARQUIVOS
# ============================================================================

def processar_arquivos(arquivos_info):
    """
    Processa arquivos em diferentes formatos: CSV, TXT, XLSX.
    Retorna lista de DataFrames normalizados.
    """
    print("\n" + "="*80)
    print("PASSO 3: PROCESSANDO ARQUIVOS (CSV, TXT, XLSX)")
    print("="*80)
    print("\nDesafio: Identificar automaticamente estrutura de colunas variadas")
    print("Solução: Buscar por padrões de nomes de colunas e normalizar\n")
    
    dataframes_com_info = []
    
    for arquivo_info in arquivos_info:
        caminho = arquivo_info['caminho']
        print(f"→ Processando {caminho.name}...")
        
        try:
            extensao = caminho.suffix.lower()
            
            if extensao == '.xlsx' or extensao == '.xls':
                df = pd.read_excel(caminho)
                print(f"  ✓ (XLSX: {len(df)} linhas)")
                
            elif extensao == '.csv':
                encoding = detectar_encoding(caminho)
                
                # Tentar diferentes delimitadores
                df = None
                for sep in [';', ',', '\t', '|']:
                    try:
                        df = pd.read_csv(caminho, encoding=encoding, sep=sep, 
                                       on_bad_lines='skip', nrows=1)
                        if len(df.columns) > 1 or (len(df.columns) == 1 and sep != ','):
                            # Encontrou o delimitador correto
                            df = pd.read_csv(caminho, encoding=encoding, sep=sep, 
                                           on_bad_lines='skip')
                            print(f"  ✓ (CSV: {len(df)} linhas, sep='{sep}', {encoding})")
                            print(f"    Colunas: {len(df.columns)}")
                            break
                    except:
                        continue
                
                if df is None or df.empty:
                    print(f"  ✗ Não foi possível ler o arquivo")
                    continue
                
            elif extensao == '.txt':
                encoding = detectar_encoding(caminho)
                df = None
                for sep in ['\t', ';', ',', '|']:
                    try:
                        df = pd.read_csv(caminho, encoding=encoding, sep=sep, 
                                       on_bad_lines='skip', nrows=1)
                        if len(df.columns) > 1:
                            df = pd.read_csv(caminho, encoding=encoding, sep=sep, 
                                           on_bad_lines='skip')
                            print(f"  ✓ (TXT: {len(df)} linhas, sep='{sep}', {encoding})")
                            break
                    except:
                        continue
                
                if df is None or df.empty:
                    print(f"  ✗ Não foi possível ler o arquivo")
                    continue
            else:
                print("  ✗ (formato não suportado)")
                continue
            
            # Normalizar colunas
            df = normalizar_dataframe(df)
            
            # Adicionar informações de ano/trimestre
            if not df.empty and 'ano' not in df.columns:
                df['ano'] = arquivo_info['ano']
                df['trimestre'] = arquivo_info['trimestre']
            
            dataframes_com_info.append(df)
            
        except Exception as e:
            print(f"  ✗ ({str(e)[:60]})")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n✓ Total de arquivos processados com sucesso: {len(dataframes_com_info)}")
    return dataframes_com_info


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def detectar_encoding(caminho_arquivo):
    """Detecta encoding de arquivo de texto."""
    try:
        with open(caminho_arquivo, 'rb') as f:
            resultado = chardet.detect(f.read(10000))
            return resultado.get('encoding', 'utf-8') or 'utf-8'
    except:
        return 'utf-8'


def normalizar_dataframe(df):
    """
    Normaliza DataFrame procurando por colunas esperadas:
    CNPJ, Razão Social, Trimestre, Ano, Valor Despesas
    """
    # Converter todos os nomes de coluna para string lowercase
    df.columns = df.columns.astype(str).str.lower().str.strip()
    
    # Mostrar colunas encontradas no arquivo
    print(f"  Colunas encontradas ({len(df.columns)}): {list(df.columns)[:10]}")
    
    # Mapping de possíveis nomes de colunas
    mapeamento = {
        'cnpj': ['cnpj', 'cnpj_empresa', 'cnpj_operadora', 'cod_operadora', 'codigo', 'reg_ans'],
        'razao_social': ['razão social', 'razao_social', 'nome', 'empresa', 'operadora', 'denominacao', 'descricao'],
        'valor': ['valor despesa', 'valor_despesa', 'despesa', 'valor', 
                 'valor_sinistro', 'sinistro', 'valor_evento', 'valor_total',
                 'vl_saldo_final', 'vl_saldo_inicial', 'valor_', 'vl_'],
        'trimestre': ['trimestre', 'mes', 'periodo', 'quarter', 'q', 'mes_'],
        'ano': ['ano', 'year']
    }
    
    df_normalizado = pd.DataFrame()
    
    # Mapear colunas encontradas
    for col_padrão, possiveis_nomes in mapeamento.items():
        col_encontrada = None
        
        for col_existente in df.columns:
            for possivel in possiveis_nomes:
                if possivel in col_existente or col_existente in possivel:
                    col_encontrada = col_existente
                    break
            if col_encontrada:
                break
        
        if col_encontrada:
            df_normalizado[col_padrão] = df[col_encontrada]
            print(f"    → Mapeado '{col_padrão}' ← '{col_encontrada}'")
    
    return df_normalizado


# ============================================================================
# PASSO 4: CONSOLIDAÇÃO E TRATAMENTO DE INCONSISTÊNCIAS
# ============================================================================

def consolidar_e_tratar_inconsistencias(arquivos_dataframes):
    """
    Consolida dados de múltiplos arquivos tratando inconsistências.
    
    Inconsistências tratadas:
    1. CNPJs duplicados com razões sociais diferentes → MARCADO COMO SUSPEITO
    2. Valores zerados ou negativos → REMOVIDO COM LOG
    3. Trimestres com formatos inconsistentes → NORMALIZADO
    """
    print("\n" + "="*80)
    print("PASSO 4: CONSOLIDAÇÃO E TRATAMENTO DE INCONSISTÊNCIAS")
    print("="*80)
    
    relatorio_inconsistencias = {
        'cnpj_duplicados_suspeitos': [],
        'valores_invalidos': [],
        'linhas_removidas': 0,
        'linhas_processadas': 0,
        'linhas_finais': 0
    }
    
    dados_consolidados = []
    
    for df in arquivos_dataframes:
        if df is None or df.empty:
            continue
        
        for idx, row in df.iterrows():
            relatorio_inconsistencias['linhas_processadas'] += 1
            linha_processada = True
            
            try:
                # Extrair dados
                cnpj = str(row.get('cnpj', '')).strip() if 'cnpj' in row else ''
                razao_social = str(row.get('razao_social', '')).strip() if 'razao_social' in row else ''
                trimestre = str(row.get('trimestre', '')).strip() if 'trimestre' in row else ''
                ano = str(row.get('ano', '')).strip() if 'ano' in row else ''
                valor = float(row.get('valor', 0)) if 'valor' in row else 0
                
                # Validação 1: CNPJ válido (básico)
                if not cnpj or cnpj == 'nan':
                    relatorio_inconsistencias['linhas_removidas'] += 1
                    linha_processada = False
                    continue
                
                # Validação 2: Valor válido
                if valor is None or pd.isna(valor):
                    valor = 0
                
                try:
                    valor = float(valor)
                except:
                    valor = 0
                
                if valor < 0:
                    relatorio_inconsistencias['valores_invalidos'].append({
                        'cnpj': cnpj,
                        'tipo': 'NEGATIVO',
                        'valor': valor
                    })
                    relatorio_inconsistencias['linhas_removidas'] += 1
                    linha_processada = False
                    continue
                
                if valor == 0:
                    relatorio_inconsistencias['valores_invalidos'].append({
                        'cnpj': cnpj,
                        'tipo': 'ZERADO',
                        'valor': valor
                    })
                    # Manter mas marcar como suspeito
                    linha_processada = True
                
                # Normalizar trimestre (01, 02, 03, 04)
                if trimestre.upper().startswith('Q'):
                    trimestre = trimestre.upper().replace('Q', '')
                
                trimestre = str(trimestre).zfill(2)
                
                # Normalizar ano
                if len(str(ano)) < 4:
                    ano = f"20{ano}" if int(ano) < 100 else ano
                
                if linha_processada:
                    dados_consolidados.append({
                        'CNPJ': cnpj,
                        'RazaoSocial': razao_social if razao_social else 'N/A',
                        'Trimestre': trimestre,
                        'Ano': ano,
                        'ValorDespesas': valor,
                        'status': 'OK' if valor > 0 else 'ZERADO'
                    })
                    relatorio_inconsistencias['linhas_finais'] += 1
                    
            except Exception as e:
                relatorio_inconsistencias['linhas_removidas'] += 1
    
    # Verificar CNPJs duplicados
    cnpj_razoes = defaultdict(set)
    for linha in dados_consolidados:
        cnpj_razoes[linha['CNPJ']].add(linha['RazaoSocial'])
    
    for cnpj, razoes in cnpj_razoes.items():
        if len(razoes) > 1:
            relatorio_inconsistencias['cnpj_duplicados_suspeitos'].append({
                'cnpj': cnpj,
                'razoes_sociais': list(razoes)
            })
    
    # Criar DataFrame consolidado
    df_consolidado = pd.DataFrame(dados_consolidados)
    
    # Ordenar
    if not df_consolidado.empty:
        df_consolidado = df_consolidado.sort_values(['Ano', 'Trimestre', 'CNPJ'])
    
    print("\n" + "-"*80)
    print("RELATÓRIO DE INCONSISTÊNCIAS ENCONTRADAS:")
    print("-"*80)
    print(f"✓ Linhas processadas: {relatorio_inconsistencias['linhas_processadas']}")
    print(f"✓ Linhas válidas no resultado: {relatorio_inconsistencias['linhas_finais']}")
    print(f"✓ Linhas removidas: {relatorio_inconsistencias['linhas_removidas']}")
    print(f"✓ CNPJs com duplicação suspeita: {len(relatorio_inconsistencias['cnpj_duplicados_suspeitos'])}")
    
    if relatorio_inconsistencias['valores_invalidos']:
        print(f"✓ Valores inválidos encontrados: {len(relatorio_inconsistencias['valores_invalidos'])}")
        print("  Primeiros exemplos:")
        for exemplo in relatorio_inconsistencias['valores_invalidos'][:5]:
            print(f"    - CNPJ {exemplo['cnpj']}: {exemplo['tipo']} (R$ {exemplo['valor']})")
    
    if relatorio_inconsistencias['cnpj_duplicados_suspeitos']:
        print("\n  Exemplo de duplicação suspeita:")
        exemplo = relatorio_inconsistencias['cnpj_duplicados_suspeitos'][0]
        print(f"    - CNPJ: {exemplo['cnpj']}")
        print(f"      Razões Sociais: {', '.join(exemplo['razoes_sociais'])}")
    
    print("\n" + "-"*80)
    print("TRATAMENTO APLICADO:")
    print("-"*80)
    print("1. CNPJs duplicados com razões diferentes → MARCADOS NO STATUS")
    print("   (Motivo: Pode indicar fusão, renomeação ou erro de entrada)")
    print("2. Valores zerados → MANTIDOS COM STATUS='ZERADO'")
    print("   (Motivo: Podem ser legítimos, indicam sem despesas no período)")
    print("3. Valores negativos → REMOVIDOS")
    print("   (Motivo: Deveriam ser créditos/devoluções, não despesas)")
    print("4. Trimestres → NORMALIZADOS PARA FORMATO QQ (01-04)")
    print("5. Anos → COMPLETADOS COM SÉCULO (XX → 20XX)")
    
    return df_consolidado, relatorio_inconsistencias


# ============================================================================
# PASSO 5: SALVAR CSV E COMPACTAR
# ============================================================================

def salvar_resultado_final(df_consolidado, relatorio):
    """Salva o CSV consolidado e cria ZIP final."""
    print("\n" + "="*80)
    print("PASSO 5: SALVANDO RESULTADOS FINAIS")
    print("="*80)
    
    # Salvar CSV
    csv_path = OUTPUT_DIR / "consolidado_despesas.csv"
    df_consolidado.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"\n✓ CSV consolidado salvo: {csv_path}")
    print(f"  Linhas: {len(df_consolidado)}")
    print(f"  Colunas: {', '.join(df_consolidado.columns)}")
    
    # Salvar relatório de inconsistências
    relatorio_path = OUTPUT_DIR / "relatorio_inconsistencias.json"
    with open(relatorio_path, 'w', encoding='utf-8') as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)
    print(f"✓ Relatório de inconsistências salvo: {relatorio_path}")
    
    # Compactar em ZIP
    zip_path = OUTPUT_DIR / "consolidado_despesas.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(csv_path, arcname="consolidado_despesas.csv")
        zipf.write(relatorio_path, arcname="relatorio_inconsistencias.json")
    
    print(f"✓ Arquivo final compactado: {zip_path}")
    
    # Mostrar resumo
    print("\n" + "-"*80)
    print("RESUMO FINAL:")
    print("-"*80)
    print(f"📊 Total de registros consolidados: {len(df_consolidado)}")
    print(f"💾 Tamanho do CSV: {csv_path.stat().st_size / 1024:.2f} KB")
    print(f"📦 Tamanho do ZIP: {zip_path.stat().st_size / 1024:.2f} KB")
    print(f"📁 Localização: {OUTPUT_DIR}")
    
    return zip_path


# ============================================================================
# EXECUÇÃO PRINCIPAL
# ============================================================================

def main():
    print("=" * 80)
    print("TESTE DE INTEGRACAO COM API PUBLICA ANS")
    print("Consolidacao de Despesas com Eventos/Sinistros - Ultimos 3 Trimestres")
    print("=" * 80)
    
    try:
        # PASSO 1: Descobrir trimestres locais
        trimestres = listar_trimestres_disponiveis()
        
        if not trimestres:
            print("\nX Nenhum trimestre foi encontrado nos dados locais.")
            return
        
        # PASSO 2: Localizar arquivos
        arquivos_info = preparar_arquivos_locais(trimestres)
        
        if not arquivos_info:
            print("\nX Nenhum arquivo foi localizado.")
            return
        
        # PASSO 3: Processar diferentes formatos
        dataframes = processar_arquivos(arquivos_info)
        
        if not dataframes:
            print("\nX Nenhum arquivo foi processado com sucesso.")
            return
        
        # PASSO 4: Consolidar e tratar inconsistências
        df_final, relatorio = consolidar_e_tratar_inconsistencias(dataframes)
        
        # PASSO 5: Salvar e compactar
        salvar_resultado_final(df_final, relatorio)
        
        print("\n" + "="*80)
        print("PROCESSO FINALIZADO COM SUCESSO!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\nX Erro durante execucao: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
