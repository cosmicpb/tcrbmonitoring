#!/usr/bin/env python3
"""
Debug da página 12 que está retornando 392 observações
"""

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://apps.aavso.org/webobs/results/?star=t+crb&num_results=200&obs_types=all&page="

def debug_page(page_num):
    """Analisa página em detalhes"""
    url = BASE_URL + str(page_num)
    print(f"🔍 Analisando página {page_num}")
    print(f"   URL: {url}")
    print()
    
    response = requests.get(url, timeout=30)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table', class_='observations')
    
    if not table:
        print("❌ Tabela não encontrada!")
        return
    
    # Método ANTIGO (bugado)
    all_obs = table.find_all('tr', class_='obs')
    print(f"📊 Método ANTIGO (find_all com class_='obs'):")
    print(f"   Total de linhas: {len(all_obs)}")
    
    # Analisa as classes
    classes_count = {}
    for row in all_obs:
        classes = ' '.join(row.get('class', []))
        classes_count[classes] = classes_count.get(classes, 0) + 1
    
    print(f"\n📝 Classes encontradas:")
    for cls, count in sorted(classes_count.items()):
        print(f"   '{cls}': {count} linhas")
    
    # Método NOVO (corrigido)
    filtered_rows = [row for row in all_obs if 'obs-detail-tr' not in row.get('class', [])]
    print(f"\n✅ Método NOVO (filtrando 'obs-detail-tr'):")
    print(f"   Linhas após filtro: {len(filtered_rows)}")
    
    # Diferença
    detail_rows = [row for row in all_obs if 'obs-detail-tr' in row.get('class', [])]
    print(f"\n🔍 Análise:")
    print(f"   Linhas de Details: {len(detail_rows)}")
    print(f"   Diferença: {len(all_obs) - len(filtered_rows)}")
    
    # Mostra exemplo de linha de Detail
    if detail_rows:
        print(f"\n📄 Exemplo de linha Detail:")
        detail = detail_rows[0]
        print(f"   Classes: {detail.get('class', [])}")
        print(f"   Conteúdo (primeiros 200 chars): {str(detail)[:200]}...")
    
    # Mostra exemplo de linha principal
    if filtered_rows:
        print(f"\n📄 Exemplo de linha Principal:")
        main = filtered_rows[0]
        print(f"   Classes: {main.get('class', [])}")
        cols = main.find_all('td')
        if len(cols) >= 8:
            print(f"   JD: {cols[2].text.strip()}")
            print(f"   Magnitude: {cols[4].text.strip()}")
            print(f"   Observer: {cols[7].text.strip()}")
    
    print(f"\n{'='*60}")
    if len(filtered_rows) >= 190 and len(filtered_rows) <= 210:
        print("✅ FILTRO FUNCIONANDO! (~200 observações)")
    else:
        print(f"⚠️  Esperado: ~200 obs, Obtido: {len(filtered_rows)}")

if __name__ == "__main__":
    print("=" * 60)
    print("DEBUG DA PÁGINA 12")
    print("=" * 60)
    print()
    
    debug_page(12)