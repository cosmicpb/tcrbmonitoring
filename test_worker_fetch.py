"""
Script para testar o fetch do HTML como o Cloudflare Worker faz
"""
import asyncio
from js import fetch

async def test_fetch():
    """Testa o fetch da página AAVSO"""
    url = "https://apps.aavso.org/webobs/results/?star=t+crb&num_results=20&obs_types=all&page=1"
    
    print(f"Fazendo fetch de: {url}")
    response = await fetch(url)
    html = await response.text()
    
    print(f"\n=== TAMANHO DO HTML: {len(html)} caracteres ===\n")
    
    # Verifica se tem a tabela
    if '<table class="observations">' in html:
        print("✅ Encontrou: <table class=\"observations\">")
    elif '<table id="results"' in html:
        print("✅ Encontrou: <table id=\"results\"")
    elif '<table' in html:
        print("✅ Encontrou: <table>")
        # Mostra o primeiro <table> encontrado
        table_start = html.find('<table')
        table_snippet = html[table_start:table_start+200]
        print(f"Snippet: {table_snippet}")
    else:
        print("❌ NENHUMA TABELA ENCONTRADA!")
    
    # Verifica tbody
    if '<tbody>' in html:
        print("✅ Encontrou: <tbody>")
        tbody_start = html.find('<tbody>')
        tbody_end = html.find('</tbody>', tbody_start)
        tbody = html[tbody_start:tbody_end]
        print(f"Tamanho do tbody: {len(tbody)} caracteres")
        
        # Conta linhas <tr>
        tr_count = tbody.count('<tr')
        print(f"Número de <tr> no tbody: {tr_count}")
        
        # Mostra primeiras linhas
        print("\n=== PRIMEIRAS 500 CARACTERES DO TBODY ===")
        print(tbody[:500])
    else:
        print("❌ NENHUM TBODY ENCONTRADO!")
    
    # Salva HTML para análise
    with open('worker_html_debug.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("\n✅ HTML salvo em: worker_html_debug.html")

# Executa
asyncio.run(test_fetch())