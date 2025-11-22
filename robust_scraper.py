#!/usr/bin/env python3
"""
Scraper Robusto para Coleta Massiva de Dados Históricos - T CrB (AAVSO)

Características:
- Retry automático (2 tentativas por página)
- Logs detalhados em arquivo
- Checkpoint system (retoma de onde parou)
- Lista de páginas com falha para retry posterior
- Salvamento em batches para evitar perda de dados
- Multiprocessing para velocidade
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from multiprocessing import Pool, Manager, cpu_count
import sys

# ==================== CONFIGURAÇÕES ====================

BASE_URL = "https://apps.aavso.org/webobs/results/?star=t+crb&num_results=200&obs_types=all&page="
DB_PATH = "data/tcrb_observations.db"
LOG_DIR = "logs"
CHECKPOINT_FILE = "data/scraper_checkpoint.json"
FAILED_PAGES_FILE = "data/failed_pages.json"

MAX_RETRIES = 2  # Tentativas por página
NUM_WORKERS = min(cpu_count() * 2, 3)
BATCH_SIZE = 1  # Salva após cada página (~200 obs) - máxima segurança
REQUEST_TIMEOUT = 30

# ==================== SETUP DE LOGS ====================

Path(LOG_DIR).mkdir(exist_ok=True)
Path("data").mkdir(exist_ok=True)

log_filename = f"{LOG_DIR}/scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# ==================== FUNÇÕES DE CHECKPOINT ====================

def load_checkpoint():
    """Carrega checkpoint se existir"""
    if Path(CHECKPOINT_FILE).exists():
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def save_checkpoint(data):
    """Salva checkpoint com páginas completadas"""
    try:
        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        completed = len(data.get('completed_pages', []))
        logger.info(f"✅ Checkpoint salvo: {completed} páginas completadas")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar checkpoint: {e}")

def load_failed_pages():
    """Carrega lista de páginas com falha"""
    if Path(FAILED_PAGES_FILE).exists():
        try:
            with open(FAILED_PAGES_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_failed_pages(pages):
    """Salva lista de páginas com falha"""
    try:
        with open(FAILED_PAGES_FILE, 'w') as f:
            json.dump(pages, f, indent=2)
        logger.info(f"💾 Páginas com falha salvas: {len(pages)}")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar páginas com falha: {e}")

# ==================== BANCO DE DADOS ====================

def init_database():
    """Inicializa banco de dados"""
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
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jd ON observations(jd)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_calendar_date ON observations(calendar_date)")
    
    conn.commit()
    conn.close()
    logger.info("✅ Banco de dados inicializado")

# ==================== PARSING ====================

def parse_calendar_date(date_str):
    """
    Converte data do formato AAVSO para dd/MM/yyyy HH:mm
    Entrada: "2025 Nov. 08.06528"
    Saída: "08/11/2025 01:34"
    """
    try:
        date_str = date_str.strip()
        parts = date_str.split()
        if len(parts) < 3:
            return date_str
        
        year = int(parts[0])
        month_str = parts[1].replace('.', '').strip()
        day_decimal = float(parts[2])
        
        months = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        month = months.get(month_str, 1)
        day = int(day_decimal)
        decimal_part = day_decimal - day
        hours = decimal_part * 24
        minutes = (hours - int(hours)) * 60
        
        dt = datetime(year, month, day, int(hours), int(minutes))
        return dt.strftime("%d/%m/%Y %H:%M")
        
    except Exception as e:
        logger.warning(f"⚠️ Erro ao converter data '{date_str}': {e}")
        return date_str

# ==================== SCRAPING ====================

def scrape_page(page_num, retry_count=0):
    """Coleta dados de uma página específica"""
    url = BASE_URL + str(page_num)
    
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        
        # Log do status code
        if response.status_code != 200:
            logger.warning(f"⚠️ Página {page_num}: HTTP {response.status_code}")
        
        # Tratamento específico para rate limiting
        if response.status_code == 429:
            logger.error(f"🚫 Página {page_num}: Rate limit (429) - muitas requisições")
            if retry_count < MAX_RETRIES:
                wait_time = 60 * (retry_count + 1)  # Espera progressiva: 60s, 120s
                logger.info(f"⏳ Aguardando {wait_time}s antes de tentar novamente...")
                time.sleep(wait_time)
                return scrape_page(page_num, retry_count + 1)
            else:
                return {
                    'page': page_num,
                    'observations': [],
                    'error': f'HTTP 429 - Rate limit exceeded',
                    'retry_count': retry_count
                }
        
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', class_='observations')
        
        if not table:
            return {
                'page': page_num,
                'observations': [],
                'error': 'No table found',
                'retry_count': retry_count
            }
        
        observations = []
        # Pega APENAS linhas principais (class exatamente "obs", não "obs-detail-tr")
        all_rows = table.find_all('tr', class_='obs')
        rows = [row for row in all_rows if 'obs-detail-tr' not in row.get('class', [])]
        
        for row in rows:
            cols = row.find_all('td')
            
            # Remove células vazias do início
            non_empty_cols = [col for col in cols if col.text.strip()]
            
            if len(non_empty_cols) >= 7:
                try:
                    star = non_empty_cols[0].text.strip()
                    jd = non_empty_cols[1].text.strip()
                    calendar_date_raw = non_empty_cols[2].text.strip()
                    magnitude = non_empty_cols[3].text.strip()
                    error = non_empty_cols[4].text.strip()
                    band = non_empty_cols[5].text.strip()
                    observer = non_empty_cols[6].text.strip()
                    
                    # Remove "Details..." do observer se presente
                    if 'Details' in observer:
                        observer = observer.split('Details')[0].strip()
                    
                    # Ignora limites superiores/inferiores
                    if '<' in magnitude or '>' in magnitude:
                        continue
                    
                    mag_float = float(magnitude)
                    error_float = float(error) if error and error not in ['—', '&mdash;', ''] else None
                    calendar_date_br = parse_calendar_date(calendar_date_raw)
                    band_value = band if band and band not in ['—', '&mdash;', ''] else None
                    
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
        
        return {
            'page': page_num,
            'observations': observations,
            'error': None,
            'retry_count': retry_count
        }
    
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else 'unknown'
        logger.error(f"❌ Página {page_num}: HTTP Error {status_code} - {e}")
        
        if retry_count < MAX_RETRIES:
            wait_time = 5 * (retry_count + 1)
            logger.info(f"⏳ Aguardando {wait_time}s antes de retry...")
            time.sleep(wait_time)
            return scrape_page(page_num, retry_count + 1)
        else:
            return {
                'page': page_num,
                'observations': [],
                'error': f'HTTP {status_code}: {str(e)}',
                'retry_count': retry_count
            }
    
    except requests.exceptions.Timeout:
        logger.warning(f"⏱️ Página {page_num}: Timeout após {REQUEST_TIMEOUT}s")
        if retry_count < MAX_RETRIES:
            time.sleep(2 ** retry_count)
            return scrape_page(page_num, retry_count + 1)
        else:
            return {
                'page': page_num,
                'observations': [],
                'error': 'Timeout after retries',
                'retry_count': retry_count
            }
    
    except Exception as e:
        logger.error(f"❌ Página {page_num}: {type(e).__name__}: {e}")
        if retry_count < MAX_RETRIES:
            time.sleep(2 ** retry_count)
            return scrape_page(page_num, retry_count + 1)
        else:
            return {
                'page': page_num,
                'observations': [],
                'error': str(e),
                'retry_count': retry_count
            }

# ==================== SALVAMENTO ====================

def save_batch(observations_batch):
    """Salva lote de observações no banco"""
    if not observations_batch:
        return 0
    
    try:
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
        
        logger.info(f"💾 Batch salvo: {saved_count} novas observações")
        return saved_count
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar batch: {e}")
        return 0

# ==================== DESCOBERTA DE PÁGINAS ====================

def get_total_pages():
    """Descobre número total de páginas"""
    try:
        logger.info("🔍 Descobrindo total de páginas...")
        response = requests.get(BASE_URL + "1", timeout=REQUEST_TIMEOUT)
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
                logger.info(f"✅ Total de páginas: {max_page:,}")
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
        
        logger.info(f"✅ Total de páginas: {max_page:,}")
        return max_page if max_page > 0 else 1
        
    except Exception as e:
        logger.error(f"❌ Erro ao descobrir total de páginas: {e}")
        return 1

# ==================== PROCESSAMENTO ====================

def process_result(result, stats, lock, batch_buffer, failed_pages, completed_pages):
    """Processa resultado de uma página"""
    with lock:
        stats['pages_done'] += 1
        
        if result['error']:
            stats['errors'] += 1
            failed_pages.append(result['page'])
            logger.warning(f"❌ Página {result['page']} falhou")
        else:
            obs_count = len(result['observations'])
            stats['collected'] += obs_count
            batch_buffer.extend(result['observations'])
            completed_pages.append(result['page'])  # Marca página como completada
            
            if len(batch_buffer) >= BATCH_SIZE * 200:
                saved = save_batch(list(batch_buffer))
                stats['saved'] += saved
                stats['duplicates'] += (len(batch_buffer) - saved)
                del batch_buffer[:]  # Limpa lista do multiprocessing
                
                # Salva checkpoint com lista de páginas completadas
                save_checkpoint({
                    'completed_pages': sorted(list(completed_pages)),
                    'total_collected': stats['collected'],
                    'total_saved': stats['saved'],
                    'timestamp': datetime.now().isoformat()
                })

def print_progress(stats, start_time, total_pages, start_page):
    """Imprime progresso"""
    pages_done = stats['pages_done']
    pages_to_collect = total_pages - start_page + 1
    
    if pages_done == 0:
        return
    
    progress = (pages_done / pages_to_collect) * 100
    elapsed = time.time() - start_time
    avg_time = elapsed / pages_done
    remaining = (pages_to_collect - pages_done) * avg_time
    eta = datetime.now() + timedelta(seconds=remaining)
    
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

# ==================== MAIN ====================

def main():
    logger.info("=" * 80)
    logger.info("SCRAPER ROBUSTO - T CrB (AAVSO)")
    logger.info("=" * 80)
    logger.info(f"Log: {log_filename}")
    logger.info("")
    
    init_database()
    
    # Verifica checkpoint
    checkpoint = load_checkpoint()
    completed_pages_set = set()
    
    if checkpoint:
        completed = checkpoint.get('completed_pages', [])
        completed_pages_set = set(completed)
        logger.info(f"📌 Checkpoint encontrado: {len(completed)} páginas já coletadas")
        logger.info(f"   Total coletado: {checkpoint.get('total_collected', 0):,} observações")
        logger.info(f"   Total salvo: {checkpoint.get('total_saved', 0):,} observações")
        resume = input("Retomar de onde parou? (s/N): ").strip().lower()
        if resume != 's':
            checkpoint = None
            completed_pages_set = set()
    
    total_pages = get_total_pages()
    start_page = 1
    
    if completed_pages_set:
        remaining = total_pages - len(completed_pages_set)
        logger.info(f"📊 Páginas: {remaining:,} restantes de {total_pages:,}")
    else:
        logger.info(f"📊 Páginas: 1 até {total_pages:,}")
    logger.info(f"⚙️  Workers: {NUM_WORKERS}")
    logger.info(f"🔄 Retries: {MAX_RETRIES} por página")
    logger.info("")
    
    confirm = input("Iniciar coleta? (s/N): ").strip().lower()
    if confirm != 's':
        logger.info("❌ Cancelado")
        sys.exit(0)
    
    logger.info("=" * 80)
    logger.info("INICIANDO COLETA")
    logger.info("=" * 80)
    
    manager = Manager()
    stats = manager.dict({
        'pages_done': 0,
        'collected': 0,
        'saved': 0,
        'duplicates': 0,
        'errors': 0
    })
    lock = manager.Lock()
    batch_buffer = manager.list()
    failed_pages = manager.list()
    completed_pages = manager.list(list(completed_pages_set))  # Inicializa com páginas já completadas
    
    start_time = time.time()
    
    try:
        with Pool(processes=NUM_WORKERS) as pool:
            # Filtra páginas já completadas
            all_pages = set(range(1, total_pages + 1))
            pages_to_collect = sorted(all_pages - completed_pages_set)
            
            logger.info(f"🚀 Coletando {len(pages_to_collect):,} páginas...")
            logger.info("")
            
            for i, result in enumerate(pool.imap_unordered(scrape_page, pages_to_collect, chunksize=1)):
                process_result(result, stats, lock, batch_buffer, failed_pages, completed_pages)
                
                if i % 10 == 0 or i == len(pages_to_collect) - 1:
                    print_progress(stats, start_time, len(pages_to_collect), 0)
        
        # Salva observações restantes
        if len(batch_buffer) > 0:
            with lock:
                saved = save_batch(list(batch_buffer))
                stats['saved'] += saved
                stats['duplicates'] += (len(batch_buffer) - saved)
                del batch_buffer[:]  # Limpa lista do multiprocessing
        
        print()
        
        total_time = (time.time() - start_time) / 60
        logger.info("")
        logger.info("=" * 80)
        logger.info("COLETA FINALIZADA!")
        logger.info("=" * 80)
        logger.info(f"✅ Observações coletadas: {stats['collected']:,}")
        logger.info(f"💾 Observações salvas (novas): {stats['saved']:,}")
        logger.info(f"🔄 Duplicatas ignoradas: {stats['duplicates']:,}")
        logger.info(f"❌ Páginas com erro: {stats['errors']}")
        logger.info(f"⏱️  Tempo total: {total_time:.1f} minutos")
        logger.info(f"⚡ Velocidade: {stats['pages_done'] / total_time:.1f} páginas/min")
        logger.info(f"📁 Banco: {DB_PATH}")
        
        # Salva páginas com falha
        if len(failed_pages) > 0:
            save_failed_pages(list(failed_pages))
            logger.info(f"⚠️  {len(failed_pages)} páginas falharam - salvas em {FAILED_PAGES_FILE}")
            logger.info("   Execute novamente para tentar coletar essas páginas")
        
        # Remove checkpoint ao finalizar com sucesso
        if Path(CHECKPOINT_FILE).exists():
            Path(CHECKPOINT_FILE).unlink()
            logger.info("✅ Checkpoint removido")
        
        logger.info("")
        
    except KeyboardInterrupt:
        logger.info("")
        logger.info("")
        logger.warning("⚠️  Interrompido pelo usuário")
        logger.info("💡 Execute novamente para continuar de onde parou")
        
        # Salva checkpoint final
        if len(batch_buffer) > 0:
            saved = save_batch(list(batch_buffer))
            logger.info(f"💾 Salvou {saved} observações antes de sair")
        
        sys.exit(0)

if __name__ == "__main__":
    main()