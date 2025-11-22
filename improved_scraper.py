#!/usr/bin/env python3
"""
Scraper melhorado para coleta de observações do AAVSO
Corrige o problema de coleta de linhas de detalhes
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import logging
from datetime import datetime
import os
import sys
from typing import List, Dict, Optional, Tuple
import multiprocessing as mp
from functools import partial

# Configurações
BASE_URL = "https://apps.aavso.org/webobs/results/"
PARAMS = {
    'star': 't crb',
    'num_results': '200',  # 200 resultados por página
    'obs_types': 'all'
}

DB_PATH = 'data/tcrb_observations.db'
LOG_DIR = 'logs'
CHECKPOINT_FILE = 'data/checkpoint_improved.txt'

# Configurações de paralelização
NUM_WORKERS = 3
BATCH_SIZE = 1  # Salva após cada página
MAX_RETRIES = 2
RETRY_DELAY = 5  # segundos

# Rate limiting
REQUEST_DELAY = 1.0  # segundos entre requisições
MAX_DELAY = 300  # 5 minutos de espera máxima para HTTP 429

# Configurar logging
os.makedirs(LOG_DIR, exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = os.path.join(LOG_DIR, f'improved_scraper_{timestamp}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def init_database():
    """Inicializa o banco de dados"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            star TEXT NOT NULL,
            jd REAL NOT NULL,
            calendar_date TEXT NOT NULL,
            magnitude REAL NOT NULL,
            error TEXT,
            band TEXT NOT NULL,
            observer TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(star, jd, magnitude, band, observer)
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_jd ON observations(jd)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_star ON observations(star)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_observer ON observations(observer)')
    
    conn.commit()
    conn.close()
    logger.info(f"✓ Banco de dados inicializado: {DB_PATH}")


def load_checkpoint() -> set:
    """Carrega lista de páginas já completadas"""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            completed = set(int(line.strip()) for line in f if line.strip())
        logger.info(f"✓ Checkpoint carregado: {len(completed)} páginas completadas")
        return completed
    return set()


def save_checkpoint(page: int):
    """Salva página completada no checkpoint"""
    os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
    with open(CHECKPOINT_FILE, 'a') as f:
        f.write(f"{page}\n")


def parse_observation_row(row) -> Optional[Dict]:
    """
    Parse uma linha de observação HTML
    
    IMPORTANTE: Apenas linhas com class='obs' (não 'obs-detail-tr')
    """
    try:
        # Verifica se é uma linha de detalhes (deve ser ignorada)
        classes = row.get('class', [])
        if 'obs-detail-tr' in classes:
            return None
        
        # Verifica se é uma linha de observação válida
        if 'obs' not in classes:
            return None
        
        # Extrai todas as células
        cells = row.find_all('td')
        
        # Remove células vazias do início (colspan)
        cells = [cell for cell in cells if cell.get_text(strip=True)]
        
        # Deve ter exatamente 7 células de dados
        if len(cells) != 7:
            logger.warning(f"Linha com {len(cells)} células (esperado 7): {[c.get_text(strip=True) for c in cells]}")
            return None
        
        # Extrai dados
        star = cells[0].get_text(strip=True)
        jd = cells[1].get_text(strip=True)
        calendar_date = cells[2].get_text(strip=True)
        magnitude = cells[3].get_text(strip=True)
        error = cells[4].get_text(strip=True)
        band = cells[5].get_text(strip=True)
        observer = cells[6].get_text(strip=True)
        
        # Remove link "Details..." do observer se presente
        if 'Details' in observer:
            observer = observer.split('Details')[0].strip()
        
        # Validações básicas
        if not star or not jd or not magnitude or not band or not observer:
            logger.warning(f"Dados incompletos: star={star}, jd={jd}, mag={magnitude}, band={band}, obs={observer}")
            return None
        
        # Converte tipos
        try:
            jd_float = float(jd)
            mag_float = float(magnitude)
        except ValueError as e:
            logger.warning(f"Erro ao converter números: {e}")
            return None
        
        # Normaliza error (pode ser vazio ou "—")
        if error in ['', '—', '&mdash;']:
            error = None
        
        return {
            'star': star,
            'jd': jd_float,
            'calendar_date': calendar_date,
            'magnitude': mag_float,
            'error': error,
            'band': band,
            'observer': observer
        }
        
    except Exception as e:
        logger.error(f"Erro ao fazer parse da linha: {e}")
        return None


def scrape_page(page: int, session: requests.Session) -> Tuple[int, List[Dict], str]:
    """
    Coleta dados de uma página específica
    
    Returns:
        (page_number, observations, status)
        status: 'success', 'error', 'rate_limit'
    """
    params = PARAMS.copy()
    params['page'] = page
    
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(BASE_URL, params=params, timeout=30)
            
            # Rate limiting
            if response.status_code == 429:
                wait_time = min(REQUEST_DELAY * (2 ** attempt), MAX_DELAY)
                logger.warning(f"HTTP 429 na página {page}, aguardando {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            # Erro do servidor
            if response.status_code == 503:
                wait_time = RETRY_DELAY * (attempt + 1)
                logger.warning(f"HTTP 503 na página {page}, tentativa {attempt + 1}/{MAX_RETRIES}")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Encontra a tabela de observações
            table = soup.find('table', class_='observations')
            if not table:
                logger.error(f"Tabela não encontrada na página {page}")
                return (page, [], 'error')
            
            # Encontra APENAS linhas de observação (não detalhes)
            # Usa seletor CSS para maior precisão
            all_rows = table.find_all('tr', class_='obs')
            
            # Filtra explicitamente linhas de detalhes
            obs_rows = [row for row in all_rows if 'obs-detail-tr' not in row.get('class', [])]
            
            logger.info(f"Página {page}: {len(all_rows)} linhas totais, {len(obs_rows)} linhas de observação")
            
            # Parse cada linha
            observations = []
            for row in obs_rows:
                obs = parse_observation_row(row)
                if obs:
                    observations.append(obs)
            
            logger.info(f"✓ Página {page}: {len(observations)} observações coletadas")
            
            # Delay entre requisições
            time.sleep(REQUEST_DELAY)
            
            return (page, observations, 'success')
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout na página {page}, tentativa {attempt + 1}/{MAX_RETRIES}")
            time.sleep(RETRY_DELAY)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de rede na página {page}: {e}")
            time.sleep(RETRY_DELAY)
            
        except Exception as e:
            logger.error(f"Erro inesperado na página {page}: {e}")
            return (page, [], 'error')
    
    logger.error(f"✗ Falha após {MAX_RETRIES} tentativas na página {page}")
    return (page, [], 'error')


def save_observations(observations: List[Dict]) -> int:
    """Salva observações no banco de dados"""
    if not observations:
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    inserted = 0
    duplicates = 0
    
    for obs in observations:
        try:
            cursor.execute('''
                INSERT INTO observations (star, jd, calendar_date, magnitude, error, band, observer)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                obs['star'],
                obs['jd'],
                obs['calendar_date'],
                obs['magnitude'],
                obs['error'],
                obs['band'],
                obs['observer']
            ))
            inserted += 1
        except sqlite3.IntegrityError:
            duplicates += 1
    
    conn.commit()
    conn.close()
    
    if duplicates > 0:
        logger.info(f"  → {inserted} novas, {duplicates} duplicadas")
    
    return inserted


def worker_process(pages: List[int]) -> Tuple[int, int, int]:
    """Processo worker para coletar múltiplas páginas"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    })
    
    total_obs = 0
    success_count = 0
    error_count = 0
    
    for page in pages:
        page_num, observations, status = scrape_page(page, session)
        
        if status == 'success':
            saved = save_observations(observations)
            total_obs += saved
            success_count += 1
            save_checkpoint(page_num)
        else:
            error_count += 1
    
    return (total_obs, success_count, error_count)


def main():
    """Função principal"""
    logger.info("=" * 80)
    logger.info("SCRAPER MELHORADO - AAVSO T CrB")
    logger.info("=" * 80)
    
    # Inicializa banco
    init_database()
    
    # Carrega checkpoint
    completed_pages = load_checkpoint()
    
    # Calcula páginas a coletar
    # Baseado em 721.892 observações / 200 por página = 3.610 páginas
    total_pages = 3610
    pages_to_scrape = [p for p in range(1, total_pages + 1) if p not in completed_pages]
    
    logger.info(f"Total de páginas: {total_pages}")
    logger.info(f"Páginas completadas: {len(completed_pages)}")
    logger.info(f"Páginas restantes: {len(pages_to_scrape)}")
    
    if not pages_to_scrape:
        logger.info("✓ Todas as páginas já foram coletadas!")
        return
    
    # Divide páginas entre workers
    chunk_size = len(pages_to_scrape) // NUM_WORKERS
    page_chunks = [
        pages_to_scrape[i:i + chunk_size]
        for i in range(0, len(pages_to_scrape), chunk_size)
    ]
    
    logger.info(f"Iniciando coleta com {NUM_WORKERS} workers...")
    logger.info(f"Chunks: {[len(chunk) for chunk in page_chunks]}")
    
    start_time = time.time()
    
    # Executa em paralelo
    with mp.Pool(NUM_WORKERS) as pool:
        results = pool.map(worker_process, page_chunks)
    
    # Agrega resultados
    total_obs = sum(r[0] for r in results)
    total_success = sum(r[1] for r in results)
    total_errors = sum(r[2] for r in results)
    
    elapsed = time.time() - start_time