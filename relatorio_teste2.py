import json
import pandas as pd

print('\n' + '='*80)
print('TESTE 2 — VALIDAÇÃO, ENRIQUECIMENTO E AGREGAÇÃO DE DADOS')
print('='*80)

# Show transformation report
r = json.load(open('dados_trabalho/output/relatorio_transformacao.json'))
print('\nRESULTADO CONSOLIDADO:')
print('-'*80)
for k, v in r.items():
    print(f'  {k:.<55} {v}')

print('\n' + '='*80)
print('ARQUIVOS GERADOS:')
print('='*80)

# Show sample of enriched data
enr_df = pd.read_csv('dados_trabalho/output/consolidado_enriquecido.csv')
print(f'\n1. consolidado_enriquecido.csv')
print(f'   Linhas: {len(enr_df)}')
print(f'   Colunas: {", ".join(enr_df.columns[:8])}')
print(f'   Amostra (primeiras 3 linhas):')
print(enr_df.head(3)[['CNPJ', 'RazaoSocial', 'Trimestre', 'Ano', 'ValorDespesas', 'CNPJ_valid', 'RegistroANS', 'UF']].to_string(index=False))

# Show aggregates
print(f'\n2. aggregados_operadora_uf.csv')
agg = pd.read_csv('dados_trabalho/output/aggregados_operadora_uf.csv', sep='|')
print(f'   Grupos operadora/UF: {len(agg)}')
print(f'   Top 5 por despesa total:')
top_agg = agg.nlargest(5, 'total')[['RazaoSocial', 'UF', 'total', 'mean', 'count']]
print(top_agg.to_string(index=False))

# Show media by trimestre
print(f'\n3. media_desvio_por_operadora_uf.csv')
med_df = pd.read_csv('dados_trabalho/output/media_desvio_por_operadora_uf.csv', sep='|')
print(f'   Operadoras com dados trimestrais: {len(med_df)}')
if len(med_df) > 0:
    # Convert numeric columns
    med_df['media_trimestral'] = pd.to_numeric(med_df['media_trimestral'], errors='coerce')
    med_df['desvio_trimestral'] = pd.to_numeric(med_df['desvio_trimestral'], errors='coerce')
    print(f'   Amostra (Top 3 por média trimestral):')
    top_med = med_df.nlargest(3, 'media_trimestral')[['RazaoSocial', 'UF', 'media_trimestral', 'desvio_trimestral', 'trimestres']]
    print(top_med.to_string(index=False))

# Show invalid CNPJ counts
inv = pd.read_csv('dados_trabalho/output/invalidos_cnpj.csv')
print(f'\n4. invalidos_cnpj.csv')
print(f'   Linhas com CNPJ suspeito/inválido: {len(inv)}')

print('\n' + '='*80)
print('DECISÕES TÉCNICAS (TESTE 2)')
print('='*80)
print('''
2.1 VALIDAÇÃO DE CNPJs
  • Estratégia escolhida: Manter linhas com CNPJ inválido e flaggar com CNPJ_valid=False
  • Motivos: Preservar dados para auditoria, evitar perda automática de informação
  • Prós: Auditoria manual possível; não descarta dados potencialmente úteis
  • Contras: Agregações precisam filtrar inválidos explicitamente

2.2 ENRIQUECIMENTO COM CADASTRO
  • Estratégia escolhida: Left-join do consolidado sobre cadastro
  • Motivos: Preserva todos os registros do consolidado; cadastro é menor (<100k linhas)
  • Tratamento de sem-match: RegistroANS/Modalidade/UF = NULL (marcado no relatório)
  • Conflitos no cadastro: Detectados e reportados; primeira ocorrência usada

2.3 AGREGAÇÕES
  • Estratégia escolhida: Usar pandas.groupby em memória
  • Motivos: Resultado agregado cabe em memória (redução forte de linhas)
  • Ordenação: Não necessária antes (groupby é otimizado internamente)
  • Métricas: total, mean, std, count por operadora/UF; média trimestral com desvio

ARQUITETURA DE PROCESSAMENTO:
  • Leitura chunked: 200k linhas por vez (eficiência de memória)
  • Validação em 3 níveis: CNPJ, valores numéricos, razão social não vazia
  • Join: Left-join com deduplicação de cadastro (keep='first')
  • Agregação final: Consolidação em memória (viável dado tamanho do resultado)
''')

print('='*80)
print('PRÓXIMOS PASSOS:')
print('='*80)
print('''
1. Auditar invalidos_cnpj.csv para decisão de limpeza ou correção
2. Validar matches do cadastro (missing_in_cadastro no relatório)
3. Usar aggregados_operadora_uf.csv para análise de despesas por operadora
4. Usar media_desvio_por_operadora_uf.csv para identificar operadoras com variação alta
5. Visualizar em Excel/BI para decisões de negócio
''')
print('='*80 + '\n')
