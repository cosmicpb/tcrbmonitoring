#!/usr/bin/env python3
"""
Testa o scraper melhorado na página 7
"""

import requests
from bs4 import BeautifulSoup
import sys

BASE_URL = "https://apps.aavso.org/webobs/results/"
PARAMS = {
    'star': 't crb',
    'num_results': '200',
    'obs_types': 'all',
    'page': 7
}

def test_page_7():
    """Testa coleta da página 7"""
    print("=" * 80)
    print("TESTE DO SCRAPER MELHORADO - PÁGINA 7")
    print("=" * 80)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    })
    
    print(f"\n1. Fazendo requisição para página 7...")
    response = session.get(BASE_URL, params=PARAMS, timeout=30)
    print(f"   Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   ✗ Erro: {response.status_code}")
        return
    
    print("\n2. Parseando HTML...")
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Encontra tabela
    table = soup.find('table', class_='observations')
    if not table:
        print("   ✗ Tabela não encontrada!")
        return
    
    print("   ✓ Tabela encontrada")
    
    # Método 1: Todas as linhas com class='obs'
    print("\n3. Método 1: find_all('tr', class_='obs')")
    all_obs_rows = table.find_all('tr', class_='obs')
    print(f"   Total de linhas: {len(all_obs_rows)}")
    
    # Analisa classes
    detail_rows = [row for row in all_obs_rows if 'obs-detail-tr' in row.get('class', [])]
    main_rows = [row for row in all_obs_rows if 'obs-detail-tr' not in row.get('class', [])]
    
    print(f"   - Linhas principais (obs): {len(main_rows)}")
    print(f"   - Linhas de detalhes (obs-detail-tr): {len(detail_rows)}")
    
    # Método 2: Filtragem explícita
    print("\n4. Método 2: Filtragem explícita")
    filtered_rows = [row for row in all_obs_rows if 'obs-detail-tr' not in row.get('class', [])]
    print(f"   Linhas após filtro: {len(filtered_rows)}")
    
    # Analisa primeiras 3 linhas
    print("\n5. Análise das primeiras 3 observações:")
    for i, row in enumerate(filtered_rows[:3]):
        cells = row.find_all('td')
        # Remove células vazias
        cells = [cell for cell in cells if cell.get_text(strip=True)]
        
        print(f"\n   Observação {i+1}:")
        print(f"   - Classes: {row.get('class', [])}")
        print(f"   - ID: {row.get('id', 'N/A')}")
        print(f"   - Células: {len(cells)}")
        
        if len(cells) >= 7:
            star = cells[0].get_text(strip=True)
            jd = cells[1].get_text(strip=True)
            cal_date = cells[2].get_text(strip=True)
            mag = cells[3].get_text(strip=True)
            error = cells[4].get_text(strip=True)
            band = cells[5].get_text(strip=True)
            observer = cells[6].get_text(strip=True)
            
            # Remove "Details..." do observer
            if 'Details' in observer:
                observer = observer.split('Details')[0].strip()
            
            print(f"   - Star: {star}")
            print(f"   - JD: {jd}")
            print(f"   - Date: {cal_date}")
            print(f"   - Mag: {mag}")
            print(f"   - Error: {error if error else 'N/A'}")
            print(f"   - Band: {band}")
            print(f"   - Observer: {observer}")
    
    # Comparação com scraper antigo
    print("\n" + "=" * 80)
    print("COMPARAÇÃO COM SCRAPER ANTIGO")
    print("=" * 80)
    print(f"Scraper antigo coletaria: {len(all_obs_rows)} linhas (incluindo detalhes)")
    print(f"Scraper melhorado coleta: {len(filtered_rows)} linhas (apenas observações)")
    print(f"Diferença: {len(all_obs_rows) - len(filtered_rows)} linhas de detalhes removidas")
    
    # Validação
    print("\n" + "=" * 80)
    print("VALIDAÇÃO")
    print("=" * 80)
    
    expected = 20  # Página com num_results=200 deveria ter ~200, mas página 7 tem 20
    if len(filtered_rows) == expected:
        print(f"✓ CORRETO: {len(filtered_rows)} observações (esperado: {expected})")
    else:
        print(f"⚠ ATENÇÃO: {len(filtered_rows)} observações (esperado: ~{expected})")
    
    # Verifica se todas as linhas têm 7 células
    invalid_rows = 0
    for row in filtered_rows:
        cells = [cell for cell in row.find_all('td') if cell.get_text(strip=True)]
        if len(cells) != 7:
            invalid_rows += 1
    
    if invalid_rows == 0:
        print(f"✓ CORRETO: Todas as {len(filtered_rows)} linhas têm 7 células")
    else:
        print(f"✗ ERRO: {invalid_rows} linhas com número incorreto de células")
    
    print("\n" + "=" * 80)
    print("TESTE CONCLUÍDO")
    print("=" * 80)

if __name__ == '__main__':
    try:
        test_page_7()
    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)