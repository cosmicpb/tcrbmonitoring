#!/usr/bin/env python3
"""
Testa a correção do bug de parsing
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

DB_PATH = 'data/tcrb_observations_test.db'

print("=" * 80)
print("TESTE DA CORREÇÃO DO BUG")
print("=" * 80)

# Cria banco de teste
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        star TEXT NOT NULL,
        jd TEXT NOT NULL,
        calendar_date TEXT NOT NULL,
        magnitude REAL NOT NULL,
        error REAL,
        band TEXT,
        observer TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(star, jd, magnitude, band, observer)
    )
""")
conn.commit()
conn.close()

print("\n1. Coletando página 1...")
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
})

response = session.get(BASE_URL, params=PARAMS, timeout=30)
soup = BeautifulSoup(response.content, 'html.parser')

table = soup.find('table', class_='observations')
all_rows = table.find_all('tr', class_='obs')
rows = [row for row in all_rows if 'obs-detail-tr' not in row.get('class', [])]

print(f"   Total de linhas: {len(rows)}")

# Parse com a lógica corrigida
observations = []
for row in rows:
    cols = row.find_all('td')
    
    # Remove células vazias do início
    non_empty_cols = [col for col in cols if col.text.strip()]
    
    if len(non_empty_cols) >= 7:
        try:
            star = non_empty_cols[0].text.strip()
            jd = non_empty_cols[1].text.strip()
            calendar_date_raw = non_empty_cols[2].text.strip()
            magnitude = non_empty_cols[3].text.strip()
            error = non_empty_cols[4].text.strip()
            band = non_empty_cols[5].text.strip()
            observer = non_empty_cols[6].text.strip()
            
            # Remove "Details..." do observer se presente
            if 'Details' in observer:
                observer = observer.split('Details')[0].strip()
            
            # Ignora limites superiores/inferiores
            if '<' in magnitude or '>' in magnitude:
                continue
            
            mag_float = float(magnitude)
            error_float = float(error) if error and error not in ['—', '&mdash;', ''] else None
            
            observations.append({
                'star': star,
                'jd': jd,
                'calendar_date': calendar_date_raw,
                'magnitude': mag_float,
                'error': error_float,
                'band': band,
                'observer': observer
            })
            
        except (ValueError, IndexError) as e:
            print(f"   ⚠️ Erro no parse: {e}")
            continue

print(f"   Observações parseadas: {len(observations)}")

# Salva no banco
print("\n2. Salvando no banco de teste...")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

saved = 0
for obs in observations:
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO observations
            (star, jd, calendar_date, magnitude, error, band, observer)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            obs['star'],
            obs['jd'],
            obs['calendar_date'],
            obs['magnitude'],
            obs['error'],
            obs['band'],
            obs['observer']
        ))
        if cursor.rowcount > 0:
            saved += 1
    except Exception as e:
        print(f"   ⚠️ Erro ao salvar: {e}")

conn.commit()
conn.close()

print(f"   Salvas: {saved}")

# Verifica as 3 observações problemáticas
print("\n3. Verificando observações que estavam faltando...")
missing_jds = ['2460987.552916', '2460987.552081', '2460987.551311']

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

for jd in missing_jds:
    cursor.execute("""
        SELECT calendar_date, jd, magnitude, band, observer 
        FROM observations 
        WHERE jd = ?
    """, (jd,))
    result = cursor.fetchone()
    
    if result:
        print(f"   ✅ JD {jd}: ENCONTRADO")
        print(f"      Date: {result[0]}, Mag: {result[2]}, Band: {result[3]}, Observer: {result[4]}")
    else:
        print(f"   ❌ JD {jd}: NÃO ENCONTRADO")

conn.close()

print("\n" + "=" * 80)
print("TESTE CONCLUÍDO")
print("=" * 80)
print(f"\nBanco de teste: {DB_PATH}")
print("Se todas as 3 observações foram encontradas, a correção está OK!")