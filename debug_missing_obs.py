#!/usr/bin/env python3
"""
Debug: Por que 3 observações não foram salvas?
JDs: 2460987.552916, 2460987.552081, 2460987.551311
"""

import requests
from bs4 import BeautifulSoup
import sqlite3

BASE_URL = "https://apps.aavso.org/webobs/results/"
PARAMS = {
    'star': 't crb',
    'num_results': '200',
    'obs_types': 'all',
    'page': 1
}

DB_PATH = 'data/tcrb_observations.db'

missing_jds = [2460987.552916, 2460987.552081, 2460987.551311]

print("=" * 80)
print("DEBUG: Observações Faltando")
print("=" * 80)

# 1. Verificar no banco
print("\n1. Verificando no banco de dados...")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

for jd in missing_jds:
    cursor.execute("SELECT * FROM observations WHERE jd = ?", (jd,))
    result = cursor.fetchone()
    if result:
        print(f"   ✓ JD {jd}: ENCONTRADO no banco")
    else:
        print(f"   ✗ JD {jd}: NÃO ENCONTRADO no banco")

conn.close()

# 2. Buscar no HTML
print("\n2. Buscando no HTML da página 1...")
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
})

response = session.get(BASE_URL, params=PARAMS, timeout=30)
soup = BeautifulSoup(response.content, 'html.parser')

table = soup.find('table', class_='observations')
if not table:
    print("   ✗ Tabela não encontrada!")
    exit(1)

# Encontra todas as linhas
all_rows = table.find_all('tr', class_='obs')
obs_rows = [row for row in all_rows if 'obs-detail-tr' not in row.get('class', [])]

print(f"   Total de linhas: {len(obs_rows)}")

# Procura pelas observações faltando
print("\n3. Analisando linhas com JDs faltando...")
for jd in missing_jds:
    print(f"\n   JD: {jd}")
    found = False
    
    for i, row in enumerate(obs_rows):
        cells = row.find_all('td')
        
        # Procura pela célula com o JD
        for cell in cells:
            cell_text = cell.get_text(strip=True)
            if str(jd) in cell_text:
                found = True
                print(f"   ✓ Encontrado na linha {i}")
                
                # Mostra todas as células
                all_cells = [c.get_text(strip=True) for c in cells]
                print(f"   Células totais: {len(cells)}")
                print(f"   Células não vazias: {len([c for c in all_cells if c])}")
                
                # Remove células vazias
                non_empty = [c for c in all_cells if c]
                print(f"   Dados: {non_empty}")
                
                # Tenta fazer parse
                try:
                    # Remove células vazias do início
                    data_cells = non_empty
                    
                    if len(data_cells) >= 7:
                        star = data_cells[0]
                        jd_val = data_cells[1]
                        cal_date = data_cells[2]
                        mag = data_cells[3]
                        error = data_cells[4]
                        band = data_cells[5]
                        observer = data_cells[6]
                        
                        # Remove "Details..." do observer
                        if 'Details' in observer:
                            observer = observer.split('Details')[0].strip()
                        
                        print(f"   Parse:")
                        print(f"     Star: {star}")
                        print(f"     JD: {jd_val}")
                        print(f"     Date: {cal_date}")
                        print(f"     Mag: {mag}")
                        print(f"     Error: {error if error and error != '—' else 'NULL'}")
                        print(f"     Band: {band}")
                        print(f"     Observer: {observer}")
                        
                        # Tenta converter
                        try:
                            jd_float = float(jd_val)
                            mag_float = float(mag)
                            print(f"   ✓ Conversão OK: JD={jd_float}, Mag={mag_float}")
                        except ValueError as e:
                            print(f"   ✗ Erro na conversão: {e}")
                    else:
                        print(f"   ✗ Número insuficiente de células: {len(data_cells)}")
                        
                except Exception as e:
                    print(f"   ✗ Erro no parse: {e}")
                
                break
    
    if not found:
        print(f"   ✗ NÃO encontrado no HTML!")

print("\n" + "=" * 80)
print("DEBUG CONCLUÍDO")
print("=" * 80)