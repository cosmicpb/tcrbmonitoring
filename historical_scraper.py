#!/usr/bin/env python3
"""
Script para coletar dados históricos da estrela T CrB do portal AAVSO.
Coleta todas as observações disponíveis e salva em banco SQLite local.
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import time
from datetime import datetime
import sys

# Configurações
BASE_URL = "https://www.aavso.org/apps/webobs/results/?star=T+CrB&num_results=200&obs_types=vis&page="
DELAY_BETWEEN_REQUESTS = 1  # segundos entre requisições
MAX_RETRIES = 3  # número máximo de tentativas por página
DB_PATH = "data/tcrb_observations.db"

def init_database():
    """Inicializa o banco de dados SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            star TEXT NOT NULL,
            date_original TEXT NOT NULL,
            date_br TEXT NOT NULL,
            magnitude REAL NOT NULL,
            observer TEXT,
            obs_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(star, date_original, magnitude, observer)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado")

def parse_calendar_date(date_str):
    """
    Converte data do formato AAVSO para formato brasileiro
    Exemplo: "2458849.6250" -> "25/12/2019 03:00"
    """
    try:
        # JD (Julian Date) para datetime
        jd = float(date_str)
        # Fórmula de conversão JD para data gregoriana
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
        
        # Extrai hora da parte fracionária
        hours = (day - int(day)) * 24
        minutes = (hours - int(hours)) * 60
        
        dt = datetime(int(year), int(month), int(day), int(hours), int(minutes))
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return date_str

def get_total_pages():
    """Descobre o número total de páginas disponíveis"""
    try:
        response = requests.get(BASE_URL + "1", timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Procura pelo último link de paginação
        pagination = soup.find('div', class_='pagination')
        if pagination:
            links = pagination.find_all('a')
            if links:
                # Pega o penúltimo link (último é "Next")
                last_page_link = links[-2].get('href', '')
                if 'page=' in last_page_link:
                    return int(last_page_link.split('page=')[-1])
        
        return 1
    except Exception as e:
        print(f"❌ Erro ao descobrir total de páginas: {e}")
        return 1

def scrape_page(page_num, retry_count=0):
    """Coleta dados de uma página específica com retry automático"""
    url = BASE_URL + str(page_num)
    
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Encontra a tabela de observações
        table = soup.find('table', class_='observations')
        if not table:
            return []
        
        observations = []
        rows = table.find_all('tr')[1:]  # Pula o cabeçalho
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 4:
                date_original = cols[0].text.strip()
                magnitude = cols[1].text.strip()
                observer = cols[2].text.strip() if len(cols) > 2 else "Unknown"
                obs_type = cols[3].text.strip() if len(cols) > 3 else "vis"
                
                try:
                    mag_float = float(magnitude)
                    date_br = parse_calendar_date(date_original)
                    
                    observations.append({
                        'star': 'T CrB',
                        'date_original': date_original,
                        'date_br': date_br,
                        'magnitude': mag_float,
                        'observer': observer,
                        'obs_type': obs_type
                    })
                except ValueError:
                    continue
        
        return observations
    
    except Exception as e:
        if retry_count < MAX_RETRIES:
            print(f"⚠️  Erro na tentativa {retry_count + 1}/{MAX_RETRIES + 1}: {e}")
            print(f"   Tentando novamente em 2 segundos...")
            time.sleep(2)
            return scrape_page(page_num, retry_count + 1)
        else:
            print(f"❌ Erro após {MAX_RETRIES + 1} tentativas na página {page_num}: {e}")
            return []

def save_observations(observations):
    """Salva observações no banco de dados"""
    if not observations:
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    saved_count = 0
    for obs in observations:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO observations 
                (star, date_original, date_br, magnitude, observer, obs_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                obs['star'],
                obs['date_original'],
                obs['date_br'],
                obs['magnitude'],
                obs['observer'],
                obs['obs_type']
            ))
            if cursor.rowcount > 0:
                saved_count += 1
        except Exception as e:
            print(f"⚠️  Erro ao salvar observação: {e}")
    
    conn.commit()
    conn.close()
    
    return saved_count

def main():
    print("=" * 70)
    print("COLETOR DE DADOS HISTÓRICOS - T CrB (AAVSO)")
    print("=" * 70)
    print()
    
    # Inicializa banco
    init_database()
    print()
    
    # Descobre total de páginas
    print("Descobrindo número total de páginas...")
    total_pages = get_total_pages()
    print(f"✅ Total de páginas encontradas: {total_pages:,}")
    print(f"📊 Estimativa de observações: ~{total_pages * 200:,}")
    print()
    
    # Pergunta página inicial
    print("Opções de coleta:")
    print("  1. Começar do início (página 1)")
    print("  2. Escolher página inicial")
    print()
    
    choice = input("Escolha uma opção (1 ou 2): ").strip()
    
    start_page = 1
    if choice == '2':
        while True:
            try:
                page_input = input(f"Digite a página inicial (1-{total_pages}): ").strip()
                start_page = int(page_input)
                if 1 <= start_page <= total_pages:
                    break
                else:
                    print(f"⚠️  Por favor, digite um número entre 1 e {total_pages}")
            except ValueError:
                print("⚠️  Por favor, digite um número válido")
    
    pages_to_collect = total_pages - start_page + 1
    print()
    print(f"📋 Configuração:")
    print(f"   Página inicial: {start_page}")
    print(f"   Página final: {total_pages}")
    print(f"   Total de páginas a coletar: {pages_to_collect:,}")
    print(f"   Estimativa de observações: ~{pages_to_collect * 200:,}")
    print()
    
    # Confirmação
    print("⚠️  ATENÇÃO: Este processo pode levar várias horas!")
    print(f"   Serão feitas {pages_to_collect:,} requisições ao servidor AAVSO")
    print(f"   Com delay de {DELAY_BETWEEN_REQUESTS}s entre requisições")
    print(f"   Máximo de {MAX_RETRIES + 1} tentativas por página em caso de erro")
    print()
    
    confirm = input("Deseja continuar? (s/N): ").strip().lower()
    if confirm != 's':
        print("❌ Operação cancelada")
        sys.exit(0)
    
    print()
    print("=" * 70)
    print("INICIANDO COLETA DE DADOS")
    print("=" * 70)
    print()
    
    # Coleta dados
    total_collected = 0
    total_saved = 0
    start_time = time.time()
    
    for page in range(start_page, total_pages + 1):
        print(f"Coletando página {page}...", end=" ", flush=True)
        
        observations = scrape_page(page)
        saved = save_observations(observations)
        
        total_collected += len(observations)
        total_saved += saved
        
        # Estatísticas
        elapsed = (time.time() - start_time) / 60  # minutos
        pages_done = page - start_page + 1
        progress = (pages_done / pages_to_collect) * 100
        avg_time_per_page = elapsed / pages_done if pages_done > 0 else 0
        remaining_pages = total_pages - page
        estimated_remaining = (remaining_pages * avg_time_per_page)
        
        print(f"✅ {len(observations)} observações coletadas")
        print(f"   💾 Salvos: {saved} novos | Total coletado: {total_collected:,} | Progresso: {page}/{total_pages} ({progress:.1f}%)")
        print(f"   ⏱️  Tempo decorrido: {elapsed:.1f}min | Estimativa restante: {estimated_remaining:.1f}min")
        print()
        
        # Delay entre requisições
        if page < total_pages:
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    # Resumo final
    total_time = (time.time() - start_time) / 60
    print()
    print("=" * 70)
    print("COLETA FINALIZADA!")
    print("=" * 70)
    print(f"✅ Total de observações coletadas: {total_collected:,}")
    print(f"💾 Total de observações salvas (novas): {total_saved:,}")
    print(f"⏱️  Tempo total: {total_time:.1f} minutos")
    print(f"📁 Banco de dados: {DB_PATH}")
    print()
    print("Para consultar os dados, use:")
    print(f"  sqlite3 {DB_PATH}")
    print("  SELECT COUNT(*) FROM observations;")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Coleta interrompida pelo usuário")
        print("💡 Execute o script novamente para continuar de onde parou")
        sys.exit(0)