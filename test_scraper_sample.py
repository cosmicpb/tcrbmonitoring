#!/usr/bin/env python3
"""
Script de teste para verificar dados coletados do AAVSO
Coleta apenas 1 página e mostra os resultados
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://apps.aavso.org/webobs/results/?star=t+crb&num_results=200&obs_types=all&page="

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

def test_scrape():
    """Testa coleta de 1 página"""
    print("=" * 80)
    print("TESTE DE COLETA - AAVSO T CrB")
    print("=" * 80)
    print()
    
    page = 1
    url = BASE_URL + str(page)
    
    print(f"🌐 URL: {url}")
    print(f"⏳ Fazendo requisição...")
    print()
    
    try:
        response = requests.get(url, timeout=30)
        print(f"✅ Status: {response.status_code}")
        print(f"📦 Tamanho: {len(response.content)} bytes")
        print()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Encontra a tabela
        table = soup.find('table', class_='observations')
        
        if not table:
            print("❌ Tabela não encontrada!")
            return
        
        print("✅ Tabela encontrada!")
        print()
        
        # Processa apenas linhas principais (class="obs")
        rows = table.find_all('tr', class_='obs')
        
        print(f"📊 Total de linhas encontradas: {len(rows)}")
        print()
        
        observations = []
        
        for row in rows:
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
                    
                    observations.append({
                        'star': star,
                        'jd': jd,
                        'calendar_date': calendar_date_br,
                        'magnitude': mag_float,
                        'error': error_float,
                        'band': band_value,
                        'observer': observer
                    })
                except (ValueError, IndexError) as e:
                    continue
        
        print(f"✅ Observações processadas: {len(observations)}")
        print()
        print("=" * 80)
        print("PRIMEIRAS 10 OBSERVAÇÕES:")
        print("=" * 80)
        print()
        
        for i, obs in enumerate(observations[:10], 1):
            print(f"#{i}")
            print(f"  Estrela: {obs['star']}")
            print(f"  JD: {obs['jd']}")
            print(f"  Data BR: {obs['calendar_date']}")
            print(f"  Magnitude: {obs['magnitude']}")
            print(f"  Erro: {obs['error']}")
            print(f"  Filtro: {obs['band']}")
            print(f"  Observador: {obs['observer']}")
            print()
        
        print("=" * 80)
        print("ESTATÍSTICAS:")
        print("=" * 80)
        print(f"Total coletado: {len(observations)}")
        print(f"Com filtro: {sum(1 for o in observations if o['band'])}")
        print(f"Sem filtro: {sum(1 for o in observations if not o['band'])}")
        print(f"Com erro: {sum(1 for o in observations if o['error'])}")
        print(f"Sem erro: {sum(1 for o in observations if not o['error'])}")
        print()
        
        # Mostra distribuição de filtros
        filters = {}
        for obs in observations:
            f = obs['band'] or 'Sem filtro'
            filters[f] = filters.get(f, 0) + 1
        
        print("Distribuição de filtros:")
        for f, count in sorted(filters.items(), key=lambda x: x[1], reverse=True):
            print(f"  {f}: {count}")
        print()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    test_scrape()