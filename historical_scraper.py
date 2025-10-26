#!/usr/bin/env python3
"""
Script para coletar dados históricos da estrela T CrB do portal AAVSO.
Coleta todas as observações disponíveis e salva em banco SQLite local.
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import time
from datetime import datetime, timedelta
import sys
import threading

# Configurações
BASE_URL = "https://apps.aavso.org/webobs/results/?star=t+crb&num_results=200&obs_types=all&page="
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
        response = requests.get(BASE_URL + "1", timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Procura pela div com class="pages"
        pages_div = soup.find('div', class_='pages')
        if pages_div:
            # Procura todos os links dentro da div
            links = pages_div.find_all('a', href=True)
            max_page = 1
            
            for link in links:
                href = link.get('href', '')
                # Extrai o número da página da URL
                if 'page=' in href:
                    try:
                        page_num = int(href.split('page=')[-1].split('&')[0])
                        if page_num > max_page:
                            max_page = page_num
                    except ValueError:
                        continue
            
            if max_page > 1:
                return max_page
        
        # Fallback: procura em todos os links da página
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
        print("⚠️  Usando página 1 como padrão. Você pode especificar manualmente.")
        return 1

def scrape_page(page_num, retry_count=0):
    """Coleta dados de uma página específica com retry automático"""
    url = BASE_URL + str(page_num)
    
    # Variável para controlar o timeout visual
    request_start = time.time()
    timeout_duration = 30
    request_done = False
    
    def show_timeout_progress():
        """Mostra progresso do timeout em tempo real"""
        while not request_done:
            elapsed = time.time() - request_start
            if elapsed >= timeout_duration:
                break
            remaining = timeout_duration - elapsed
            print(f"\r   ⏳ Aguardando resposta do servidor... {remaining:.1f}s restantes", end="", flush=True)
            time.sleep(0.1)
    
    # Inicia thread para mostrar progresso
    progress_thread = threading.Thread(target=show_timeout_progress, daemon=True)
    progress_thread.start()
    
    try:
        response = requests.get(url, timeout=timeout_duration)
        request_done = True
        request_time = time.time() - request_start
        print(f"\r   ✅ Resposta recebida em {request_time:.2f}s" + " " * 40)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Encontra a tabela de observações com class='observations'
        table = soup.find('table', class_='observations')
        
        if not table:
            print(f"\r   ⚠️  Nenhuma tabela encontrada na página" + " " * 40)
            return []
        
        observations = []
        rows = table.find_all('tr')
        
        # Pula o cabeçalho (primeira linha)
        if len(rows) > 0:
            rows = rows[1:]
        
        # Cada observação ocupa 2 linhas: dados principais + detalhes
        # Vamos processar apenas as linhas ímpares (dados principais)
        for i in range(0, len(rows), 2):
            if i >= len(rows):
                break
                
            row = rows[i]
            cols = row.find_all('td')
            
            # Precisa ter pelo menos 8 colunas (conforme cabeçalho)
            if len(cols) >= 8:
                try:
                    # Colunas: '', 'Star', 'JD', 'Calendar Date', 'Magnitude', 'Error', 'Filter', 'Observer', ''
                    star = cols[1].text.strip()
                    date_jd = cols[2].text.strip()
                    date_calendar = cols[3].text.strip()
                    magnitude = cols[4].text.strip()
                    error = cols[5].text.strip()
                    filter_type = cols[6].text.strip()
                    observer = cols[7].text.strip()
                    
                    # Converte magnitude para float
                    mag_float = float(magnitude)
                    
                    # Usa a data JD para conversão
                    date_br = parse_calendar_date(date_jd)
                    
                    observations.append({
                        'star': star,
                        'date_original': date_jd,
                        'date_br': date_br,
                        'magnitude': mag_float,
                        'observer': observer,
                        'obs_type': filter_type
                    })
                except (ValueError, IndexError) as e:
                    # Ignora linhas com dados inválidos
                    continue
        
        return observations
    
    except Exception as e:
        request_done = True
        print(f"\r   ❌ Erro: {str(e)[:80]}" + " " * 40)
        if retry_count < MAX_RETRIES:
            print(f"   ⚠️  Tentativa {retry_count + 1}/{MAX_RETRIES + 1} falhou")
            print(f"   🔄 Tentando novamente em 2 segundos...")
            time.sleep(2)
            return scrape_page(page_num, retry_count + 1)
        else:
            print(f"   ❌ Falha após {MAX_RETRIES + 1} tentativas na página {page_num}")
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
    
    # Se detectou apenas 1 página, pergunta se quer especificar manualmente
    if total_pages == 1:
        print()
        print("⚠️  Apenas 1 página foi detectada automaticamente.")
        print("   Isso pode estar incorreto. Você pode:")
        print("   1. Continuar com 1 página")
        print("   2. Especificar o número total de páginas manualmente")
        print()
        
        choice = input("Escolha uma opção (1 ou 2): ").strip()
        if choice == '2':
            while True:
                try:
                    manual_pages = input("Digite o número total de páginas: ").strip()
                    total_pages = int(manual_pages)
                    if total_pages > 0:
                        print(f"✅ Usando {total_pages:,} páginas")
                        break
                    else:
                        print("⚠️  Por favor, digite um número maior que 0")
                except ValueError:
                    print("⚠️  Por favor, digite um número válido")
    
    print(f"📊 Estimativa de observações: ~{total_pages * 200:,}")
    print()
    
    # Pergunta página inicial
    print("Opções de coleta:")
    print("  1. Começar do início (página 1)")
    print("  2. Escolher página inicial")
    print()
    
    while True:
        choice = input("Escolha uma opção (1 ou 2): ").strip()
        
        if choice == '1':
            start_page = 1
            break
        elif choice == '2':
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
            break
        else:
            print("⚠️  Por favor, escolha 1 ou 2")
    
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
    total_duplicates = 0
    total_errors = 0
    start_time = time.time()
    
    print()
    
    for page in range(start_page, total_pages + 1):
        page_start = time.time()
        
        print(f"{'='*70}")
        print(f"📄 PÁGINA {page:,} de {total_pages:,}")
        print(f"{'='*70}")
        
        observations = scrape_page(page)
        
        if not observations:
            total_errors += 1
            print(f"   ⚠️  Nenhuma observação coletada (possível erro)")
        else:
            saved = save_observations(observations)
            duplicates = len(observations) - saved
            
            total_collected += len(observations)
            total_saved += saved
            total_duplicates += duplicates
            
            page_time = time.time() - page_start
            
            # Estatísticas da página
            print(f"\n   📊 ESTATÍSTICAS DA PÁGINA:")
            print(f"   ├─ Observações encontradas: {len(observations)}")
            print(f"   ├─ Novas salvas: {saved}")
            print(f"   ├─ Duplicatas ignoradas: {duplicates}")
            print(f"   └─ Tempo de processamento: {page_time:.2f}s")
            
            # Estatísticas gerais
            elapsed_min = (time.time() - start_time) / 60
            elapsed_sec = (time.time() - start_time)
            pages_done = page - start_page + 1
            progress = (pages_done / pages_to_collect) * 100
            avg_time_per_page = elapsed_sec / pages_done if pages_done > 0 else 0
            remaining_pages = total_pages - page
            estimated_remaining_sec = remaining_pages * avg_time_per_page
            estimated_remaining_min = estimated_remaining_sec / 60
            
            # Calcula ETA
            eta = datetime.now() + timedelta(seconds=estimated_remaining_sec)
            
            print(f"\n   📈 PROGRESSO GERAL:")
            print(f"   ├─ Páginas processadas: {pages_done:,} / {pages_to_collect:,} ({progress:.2f}%)")
            print(f"   ├─ Total coletado: {total_collected:,} observações")
            print(f"   ├─ Total salvo (novo): {total_saved:,} observações")
            print(f"   ├─ Total duplicatas: {total_duplicates:,} observações")
            print(f"   ├─ Páginas com erro: {total_errors}")
            print(f"   └─ Taxa de sucesso: {((pages_done - total_errors) / pages_done * 100):.1f}%")
            
            print(f"\n   ⏱️  TEMPO:")
            print(f"   ├─ Decorrido: {elapsed_min:.1f}min ({elapsed_sec:.0f}s)")
            print(f"   ├─ Média por página: {avg_time_per_page:.2f}s")
            print(f"   ├─ Estimativa restante: {estimated_remaining_min:.1f}min ({estimated_remaining_sec:.0f}s)")
            print(f"   └─ ETA (previsão): {eta.strftime('%d/%m/%Y %H:%M:%S')}")
            
            # Barra de progresso visual
            bar_length = 50
            filled = int(bar_length * progress / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"\n   [{bar}] {progress:.2f}%")
        
        print()
        
        # Delay entre requisições
        if page < total_pages:
            for i in range(DELAY_BETWEEN_REQUESTS, 0, -1):
                print(f"\r   ⏸️  Aguardando {i}s antes da próxima página...", end="", flush=True)
                time.sleep(1)
            print("\r" + " " * 60 + "\r", end="", flush=True)
    
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