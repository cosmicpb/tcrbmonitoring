#!/usr/bin/env python3
"""
Script de teste para coletar apenas 1 página de dados históricos da T CrB.
Versão simplificada e não-interativa do historical_scraper.py
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime

# Configurações
BASE_URL = "https://apps.aavso.org/webobs/results/?star=t+crb&num_results=200&obs_types=all&page="
DB_PATH = "data/tcrb_observations.db"

def init_database():
    """Inicializa o banco de dados SQLite"""
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

def parse_calendar_date(date_str):
    """Converte JD para formato brasileiro"""
    try:
        jd = float(date_str)
        jd = jd + 0.5
        z = int(jd)
        f = jd - z
        
        if z < 2299161:
            a = z
        else:
            alpha = int((z - 1867216.25) / 36524.25)
            a = z + 1 + alpha - int(alpha / 4)
        
        b = a + 1524
        c = int((b - 122.1) / 365.25)
        d = int(365.25 * c)
        e = int((b - d) / 30.6001)
        
        day = b - d - int(30.6001 * e) + f
        month = e - 1 if e < 14 else e - 13
        year = c - 4716 if month > 2 else c - 4715
        
        hours = (day - int(day)) * 24
        minutes = (hours - int(hours)) * 60
        
        dt = datetime(int(year), int(month), int(day), int(hours), int(minutes))
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return date_str

def scrape_page(page_num):
    """Coleta dados de uma página específica"""
    url = BASE_URL + str(page_num)
    
    print(f"🔍 Coletando página {page_num}...")
    print(f"   URL: {url}")
    
    response = requests.get(url, timeout=30)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    table = soup.find('table', class_='observations')
    
    if not table:
        print("❌ Tabela não encontrada!")
        return []
    
    observations = []
    rows = table.find_all('tr', class_='obs')
    
    print(f"   Encontradas {len(rows)} linhas com class='obs'")
    
    for i, row in enumerate(rows):
        cols = row.find_all('td')
        
        if len(cols) >= 8:
            try:
                star = cols[1].text.strip()
                jd = cols[2].text.strip()
                magnitude = cols[4].text.strip()
                error = cols[5].text.strip()
                band = cols[6].text.strip()
                observer = cols[7].text.strip()
                
                mag_float = float(magnitude)
                error_float = float(error) if error and error != '—' else None
                calendar_date_br = parse_calendar_date(jd)
                band_value = band if band and band != '—' else None
                
                obs = {
                    'star': star,
                    'jd': jd,
                    'calendar_date': calendar_date_br,
                    'magnitude': mag_float,
                    'error': error_float,
                    'band': band_value,
                    'observer': observer
                }
                observations.append(obs)
                
                # Mostra as primeiras 5 observações
                if i < 5:
                    print(f"\n   Observação {i+1}:")
                    print(f"      JD: {jd}")
                    print(f"      Data: {calendar_date_br}")
                    print(f"      Magnitude: {mag_float}")
                    print(f"      Erro: {error_float}")
                    print(f"      Filtro: {band_value}")
                    print(f"      Observador: {observer}")
                
            except (ValueError, IndexError) as e:
                print(f"   ⚠️  Erro ao processar linha {i+1}: {e}")
                continue
    
    return observations

def save_observations(observations):
    """Salva observações no banco"""
    if not observations:
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    saved_count = 0
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
                saved_count += 1
        except Exception as e:
            print(f"   ⚠️  Erro ao salvar: {e}")
    
    conn.commit()
    conn.close()
    
    return saved_count

def main():
    print("=" * 80)
    print("TESTE DE COLETA - T CrB (AAVSO) - 1 PÁGINA")
    print("=" * 80)
    print()
    
    init_database()
    print("✅ Banco de dados inicializado")
    print()
    
    # Coleta apenas a página 1
    observations = scrape_page(1)
    
    print()
    print("=" * 80)
    print("RESULTADO DA COLETA")
    print("=" * 80)
    print(f"✅ Observações coletadas: {len(observations)}")
    
    if observations:
        # Estatísticas
        with_error = sum(1 for obs in observations if obs['error'] is not None)
        with_band = sum(1 for obs in observations if obs['band'] is not None)
        
        print(f"   Com erro: {with_error}")
        print(f"   Com filtro: {with_band}")
        
        # Distribuição de filtros
        bands = {}
        for obs in observations:
            band = obs['band'] or 'Sem filtro'
            bands[band] = bands.get(band, 0) + 1
        
        print()
        print("Distribuição de filtros:")
        for band, count in sorted(bands.items(), key=lambda x: x[1], reverse=True):
            print(f"   {band}: {count}")
        
        # Salva no banco
        print()
        saved = save_observations(observations)
        print(f"💾 Observações salvas (novas): {saved}")
        print(f"🔄 Duplicatas ignoradas: {len(observations) - saved}")
        print(f"📁 Banco: {DB_PATH}")
    
    print()

if __name__ == "__main__":
    main()