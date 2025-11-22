#!/usr/bin/env python3
"""
Teste do scraper robusto - coleta apenas 3 páginas para validação
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

# Configurações
BASE_URL = "https://apps.aavso.org/webobs/results/?star=t+crb&num_results=200&obs_types=all&page="
DB_PATH = "data/tcrb_test.db"
LOG_DIR = "logs"
TEST_PAGES = [1, 2, 3]  # Apenas 3 páginas para teste

Path(LOG_DIR).mkdir(exist_ok=True)
Path("data").mkdir(exist_ok=True)

log_filename = f"{LOG_DIR}/test_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

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
    
    conn.commit()
    conn.close()
    logger.info("✅ Banco de dados inicializado")

def parse_calendar_date(date_str):
    """Converte data do formato AAVSO para dd/MM/yyyy HH:mm"""
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

def scrape_page(page_num):
    """Coleta dados de uma página"""
    url = BASE_URL + str(page_num)
    
    try:
        logger.info(f"🔍 Coletando página {page_num}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', class_='observations')
        
        if not table:
            logger.error(f"❌ Página {page_num}: Tabela não encontrada")
            return []
        
        observations = []
        rows = table.find_all('tr', class_='obs')  # APENAS linhas principais
        
        logger.info(f"   Encontradas {len(rows)} linhas com class='obs'")
        
        for i, row in enumerate(rows):
            cols = row.find_all('td')
            
            if len(cols) >= 8:
                try:
                    star = cols[1].text.strip()
                    jd = cols[2].text.strip()
                    calendar_date_raw = cols[3].text.strip()
                    magnitude = cols[4].text.strip()
                    error = cols[5].text.strip()
                    band = cols[6].text.strip()
                    observer = cols[7].text.strip()
                    
                    # Ignora limites superiores/inferiores
                    if '<' in magnitude or '>' in magnitude:
                        logger.debug(f"   Ignorando magnitude limite: {magnitude}")
                        continue
                    
                    mag_float = float(magnitude)
                    error_float = float(error) if error and error not in ['—', '&mdash;', ''] else None
                    calendar_date_br = parse_calendar_date(calendar_date_raw)
                    band_value = band if band and band not in ['—', '&mdash;', ''] else None
                    
                    obs = {
                        'star': star,
                        'jd': jd,
                        'calendar_date': calendar_date_br,
                        'magnitude': mag_float,
                        'error': error_float,
                        'band': band_value,
                        'observer': observer
                    }
                    observations.append(obs)
                    
                    # Mostra primeiras 3 observações de cada página
                    if i < 3:
                        logger.info(f"   Obs {i+1}: JD={jd}, Mag={mag_float}, Filter={band_value}, Obs={observer}")
                    
                except (ValueError, IndexError) as e:
                    logger.debug(f"   ⚠️ Erro ao processar linha {i+1}: {e}")
                    continue
        
        logger.info(f"✅ Página {page_num}: {len(observations)} observações coletadas")
        return observations
        
    except Exception as e:
        logger.error(f"❌ Página {page_num}: Erro {type(e).__name__}: {e}")
        return []

def save_observations(observations):
    """Salva observações no banco"""
    if not observations:
        return 0
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        saved_count = 0
        for obs in observations:
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
            except Exception as e:
                logger.debug(f"⚠️ Erro ao salvar: {e}")
        
        conn.commit()
        conn.close()
        
        return saved_count
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar batch: {e}")
        return 0

def main():
    logger.info("=" * 80)
    logger.info("TESTE DO SCRAPER ROBUSTO - 3 PÁGINAS")
    logger.info("=" * 80)
    logger.info(f"Log: {log_filename}")
    logger.info("")
    
    init_database()
    
    all_observations = []
    
    for page_num in TEST_PAGES:
        observations = scrape_page(page_num)
        all_observations.extend(observations)
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("SALVANDO DADOS")
    logger.info("=" * 80)
    
    saved = save_observations(all_observations)
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("RESULTADO")
    logger.info("=" * 80)
    logger.info(f"✅ Total coletado: {len(all_observations)}")
    logger.info(f"💾 Salvas (novas): {saved}")
    logger.info(f"🔄 Duplicatas: {len(all_observations) - saved}")
    logger.info(f"📁 Banco: {DB_PATH}")
    logger.info("")

if __name__ == "__main__":
    main()