#!/usr/bin/env python3
"""
Debug das páginas 2, 4, 6 que estão retornando ~400 observações
"""

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://apps.aavso.org/webobs/results/?star=t+crb&num_results=200&obs_types=all&page="

def debug_page(page_num):
    """Analisa página em detalhes"""
    url = BASE_URL + str(page_num)
    print(f"\n{'='*60}")
    print(f"🔍 PÁGINA {page_num}")
    print(f"{'='*60}")
    
    response = requests.get(url, timeout=30)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table', class_='observations')
    
    if not table:
        print("❌ Tabela não encontrada!")
        return
    
    # Método usado no código
    all_rows = table.find_all('tr', class_='obs')
    filtered_rows = [row for row in all_rows if 'obs-detail-tr' not in row.get('class', [])]
    
    print(f"📊 Total de linhas com class='obs': {len(all_rows)}")
    print(f"✅ Linhas após filtrar 'obs-detail-tr': {len(filtered_rows)}")
    
    # Analisa as classes
    classes_count = {}
    for row in all_rows:
        classes = ' '.join(row.get('class', []))
        classes_count[classes] = classes_count.get(classes, 0) + 1
    
    print(f"\n📝 Classes encontradas:")
    for cls, count in sorted(classes_count.items()):
        print(f"   '{cls}': {count} linhas")
    
    # Verifica se tem Details
    detail_rows = [row for row in all_rows if 'obs-detail-tr' in row.get('class', [])]
    if detail_rows:
        print(f"\n⚠️  TEM {len(detail_rows)} LINHAS DE DETAILS!")
        print(f"   Exemplo: {detail_rows[0].get('class', [])}")
    else:
        print(f"\n✅ Não tem linhas de Details")
    
    # Status
    if len(filtered_rows) >= 190 and len(filtered_rows) <= 210:
        print(f"\n✅ OK: {len(filtered_rows)} observações")
    else:
        print(f"\n❌ PROBLEMA: {len(filtered_rows)} observações (esperado ~200)")

if __name__ == "__main__":
    print("=" * 60)
    print("DEBUG DAS PÁGINAS 2, 4, 6")
    print("=" * 60)
    
    for page in [2, 4, 6]:
        debug_page(page)
    
    print(f"\n{'='*60}")
    print("FIM DO DEBUG")
    print("=" * 60)