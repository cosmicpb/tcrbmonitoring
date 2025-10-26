#!/usr/bin/env python3
"""
Script de debug para ver o HTML da página do AAVSO
"""

import requests
from bs4 import BeautifulSoup

URL = "https://apps.aavso.org/webobs/results/?star=t+crb&num_results=200&obs_types=all&page=1"

print("Fazendo requisição...")
response = requests.get(URL, timeout=30)
print(f"Status: {response.status_code}")
print()

soup = BeautifulSoup(response.content, 'html.parser')

# Procura todas as tabelas
tables = soup.find_all('table')
print(f"Total de tabelas encontradas: {len(tables)}")
print()

for i, table in enumerate(tables):
    print(f"=== TABELA {i+1} ===")
    print(f"Classes: {table.get('class', 'Sem classe')}")
    print(f"ID: {table.get('id', 'Sem ID')}")
    
    rows = table.find_all('tr')
    print(f"Total de linhas (tr): {len(rows)}")
    
    if len(rows) > 0:
        # Mostra primeira linha (cabeçalho)
        first_row = rows[0]
        headers = first_row.find_all(['th', 'td'])
        print(f"Cabeçalhos: {[h.text.strip() for h in headers]}")
        
        # Mostra segunda linha (primeira observação)
        if len(rows) > 1:
            second_row = rows[1]
            cells = second_row.find_all('td')
            print(f"Primeira observação: {[c.text.strip() for c in cells]}")
    
    print()

# Salva HTML completo para análise
with open('debug_page.html', 'w', encoding='utf-8') as f:
    f.write(response.text)

print("HTML completo salvo em: debug_page.html")