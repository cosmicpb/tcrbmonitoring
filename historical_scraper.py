#!/usr/bin/env python3
"""
Script para coletar dados históricos da estrela T CrB do portal AAVSO.
Coleta todas as observações disponíveis e salva em banco SQLite local.
Usa multiprocessing para acelerar a coleta.
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import time
from datetime import datetime, timedelta
import sys
from multiprocessing import Pool, Manager, cpu_count

# Configurações
BASE_URL = "https://apps.aavso.org/webobs/results/?star=t+crb&num_results=200&obs_types=all&page="
MAX_RETRIES = 3
DB_PATH = "data/tcrb_observations.db"
NUM_WORKERS = min(cpu_count() * 2, 2)  # Máximo de 16 workers
BATCH_SIZE = 50  # Acumula 50 páginas (~10.000 observações) antes de salvar

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

def get_total_pages():
    """Descobre o número total de páginas disponíveis"""
    try:
        response = requests.get(BASE_URL + "1", timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        pages_div = soup.find('div', class_='pages')
        if pages_div:
            links = pages_div.find_all('a', href=True)
            max_page = 1
            
            for link in links:
                href = link.get('href', '')
                if 'page=' in href:
                    try:
                        page_num = int(href.split('page=')[-1].split('&')[0])
                        if page_num > max_page:
                            max_page = page_num
                    except ValueError:
                        continue
            
            if max_page > 1:
                return max_page
        
        all_links = soup.find_all('a', href=True)
        max_page = 1
        
        for link in all_links:
            href = link.get('href', '')
            if 'page=' in href and 'star=t+crb' in href.lower():
                try:
                    page_num = int(href.split('page=')[-1].split('&')[0])
                    if page_num > max_page:
                        max_page = page_num
                except ValueError:
                    continue
        
        return max_page if max_page > 0 else 1
        
    except Exception as e:
        print(f"❌ Erro ao descobrir total de páginas: {e}")
        return 1

def scrape_page(page_num, retry_count=0):
    """Coleta dados de uma página específica"""
    url = BASE_URL + str(page_num)
    
    try:
        response = requests.get(url, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        table = soup.find('table', class_='observations')
        
        if not table:
            return {'page': page_num, 'observations': [], 'error': 'No table'}
        
        observations = []
        rows = table.find_all('tr', class_='obs')
        
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
                except (ValueError, IndexError):
                    continue
        
        return {'page': page_num, 'observations': observations, 'error': None}
    
    except Exception as e:
        if retry_count < MAX_RETRIES:
            time.sleep(2)
            return scrape_page(page_num, retry_count + 1)
        else:
            return {'page': page_num, 'observations': [], 'error': str(e)}

def save_batch(observations_batch):
    """Salva um lote de observações no banco"""
    if not observations_batch:
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    saved_count = 0
    for obs in observations_batch:
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
        except:
            pass
    
    conn.commit()
    conn.close()
    
    return saved_count

def process_result(result, stats, lock, batch_buffer):
    """Processa resultado e atualiza estatísticas"""
    with lock:
        stats['pages_done'] += 1
        
        if result['error']:
            stats['errors'] += 1
        else:
            obs_count = len(result['observations'])
            stats['collected'] += obs_count
            
            # Adiciona observações ao buffer
            batch_buffer.extend(result['observations'])
            
            # Salva quando atingir o tamanho do batch
            if len(batch_buffer) >= BATCH_SIZE * 200:  # ~10.000 observações
                saved = save_batch(batch_buffer)
                stats['saved'] += saved
                stats['duplicates'] += (len(batch_buffer) - saved)
                batch_buffer.clear()

def print_progress(stats, start_time, total_pages, start_page):
    """Imprime progresso em tempo real"""
    pages_done = stats['pages_done']
    pages_to_collect = total_pages - start_page + 1
    
    if pages_done == 0:
        return
    
    progress = (pages_done / pages_to_collect) * 100
    elapsed_sec = time.time() - start_time
    avg_time_per_page = elapsed_sec / pages_done
    remaining_pages = total_pages - start_page - pages_done + 1
    estimated_remaining_sec = remaining_pages * avg_time_per_page
    eta = datetime.now() + timedelta(seconds=estimated_remaining_sec)
    
    bar_length = 40
    filled = int(bar_length * progress / 100)
    bar = '█' * filled + '░' * (bar_length - filled)
    
    print(f"\r[{bar}] {progress:.1f}% | "
          f"Páginas: {pages_done:,}/{pages_to_collect:,} | "
          f"Coletadas: {stats['collected']:,} | "
          f"Salvas: {stats['saved']:,} | "
          f"Erros: {stats['errors']} | "
          f"ETA: {eta.strftime('%H:%M:%S')}", 
          end='', flush=True)

def main():
    print("=" * 80)
    print("COLETOR DE DADOS HISTÓRICOS - T CrB (AAVSO) - MULTIPROCESSING")
    print("=" * 80)
    print()
    
    init_database()
    print("✅ Banco de dados inicializado")
    print()
    
    print("Descobrindo número total de páginas...")
    total_pages = get_total_pages()
    print(f"✅ Total de páginas encontradas: {total_pages:,}")
    
    if total_pages == 1:
        print()
        print("⚠️  Apenas 1 página detectada. Você pode:")
        print("   1. Continuar com 1 página")
        print("   2. Especificar manualmente")
        print()
        
        choice = input("Escolha (1 ou 2): ").strip()
        if choice == '2':
            while True:
                try:
                    total_pages = int(input("Digite o total de páginas: ").strip())
                    if total_pages > 0:
                        print(f"✅ Usando {total_pages:,} páginas")
                        break
                    else:
                        print("⚠️  Digite um número maior que 0")
                except ValueError:
                    print("⚠️  Digite um número válido")
    
    print(f"📊 Estimativa: ~{total_pages * 200:,} observações")
    print()
    
    print("Opções de coleta:")
    print("  1. Começar do início (página 1)")
    print("  2. Escolher página inicial")
    print()
    
    while True:
        choice = input("Escolha (1 ou 2): ").strip()
        
        if choice == '1':
            start_page = 1
            break
        elif choice == '2':
            while True:
                try:
                    start_page = int(input(f"Página inicial (1-{total_pages}): ").strip())
                    if 1 <= start_page <= total_pages:
                        break
                    else:
                        print(f"⚠️  Digite entre 1 e {total_pages}")
                except ValueError:
                    print("⚠️  Digite um número válido")
            break
        else:
            print("⚠️  Escolha 1 ou 2")
    
    pages_to_collect = total_pages - start_page + 1
    print()
    print(f"📋 Configuração:")
    print(f"   Página inicial: {start_page}")
    print(f"   Página final: {total_pages}")
    print(f"   Total a coletar: {pages_to_collect:,} páginas")
    print(f"   Estimativa: ~{pages_to_collect * 200:,} observações")
    print(f"   Workers paralelos: {NUM_WORKERS}")
    print()
    
    print("⚠️  ATENÇÃO: Multiprocessing ativado!")
    print(f"   {NUM_WORKERS} workers em paralelo")
    print(f"   Máximo {MAX_RETRIES + 1} tentativas por página")
    print()
    
    confirm = input("Continuar? (s/N): ").strip().lower()
    if confirm != 's':
        print("❌ Cancelado")
        sys.exit(0)
    
    print()
    print("=" * 80)
    print("INICIANDO COLETA")
    print("=" * 80)
    print()
    
    manager = Manager()
    stats = manager.dict({
        'pages_done': 0,
        'collected': 0,
        'saved': 0,
        'duplicates': 0,
        'errors': 0
    })
    lock = manager.Lock()
    batch_buffer = manager.list()  # Buffer compartilhado para acumular observações
    
    start_time = time.time()
    
    print(f"🚀 Iniciando {NUM_WORKERS} workers para processar {pages_to_collect:,} páginas...")
    print()
    
    with Pool(processes=NUM_WORKERS) as pool:
        pages = list(range(start_page, total_pages + 1))
        
        # Usa imap com chunksize menor para melhor distribuição
        for i, result in enumerate(pool.imap_unordered(scrape_page, pages, chunksize=1)):
            process_result(result, stats, lock, batch_buffer)
            
            # Atualiza progresso a cada 10 páginas para não sobrecarregar o terminal
            if i % 10 == 0 or i == len(pages) - 1:
                print_progress(stats, start_time, total_pages, start_page)
    
    # Salva observações restantes no buffer
    if len(batch_buffer) > 0:
        with lock:
            saved = save_batch(list(batch_buffer))
            stats['saved'] += saved
            stats['duplicates'] += (len(batch_buffer) - saved)
            batch_buffer.clear()
    
    print()
    
    total_time = (time.time() - start_time) / 60
    print()
    print("=" * 80)
    print("COLETA FINALIZADA!")
    print("=" * 80)
    print(f"✅ Observações coletadas: {stats['collected']:,}")
    print(f"💾 Observações salvas (novas): {stats['saved']:,}")
    print(f"🔄 Duplicatas ignoradas: {stats['duplicates']:,}")
    print(f"❌ Páginas com erro: {stats['errors']}")
    print(f"⏱️  Tempo total: {total_time:.1f} minutos")
    print(f"⚡ Velocidade: {stats['pages_done'] / total_time:.1f} páginas/min")
    print(f"📁 Banco: {DB_PATH}")
    print()
    print("Consultar dados:")
    print(f"  sqlite3 {DB_PATH}")
    print("  SELECT COUNT(*) FROM observations;")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido pelo usuário")
        print("💡 Execute novamente para continuar")
        sys.exit(0)