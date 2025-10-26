"""
Módulo de web scraping para coletar dados da estrela T CrB do portal AAVSO
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, Optional
import re


def parse_calendar_date(calendar_date: str) -> str:
    """
    Converte data do formato AAVSO para dd/MM/YYYY HH:mm
    Exemplo: "2025 Oct. 26.07083" -> "26/10/2025 01:42"
    """
    try:
        # Parse: "2025 Oct. 26.07083"
        parts = calendar_date.split()
        year = parts[0]
        month_str = parts[1].replace('.', '')
        day_decimal = parts[2]
        
        # Converte mês para número
        months = {
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
            'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
        }
        month = months.get(month_str, '01')
        
        # Separa dia e fração decimal
        day_parts = day_decimal.split('.')
        day = day_parts[0].zfill(2)
        
        # Converte fração decimal para horas e minutos
        if len(day_parts) > 1:
            fraction = float('0.' + day_parts[1])
            hours = int(fraction * 24)
            minutes = int((fraction * 24 - hours) * 60)
        else:
            hours = 0
            minutes = 0
        
        return f"{day}/{month}/{year} {hours:02d}:{minutes:02d}"
    except:
        # Se falhar, retorna a data original
        return calendar_date


class TCrbScraper:
    """Scraper para dados de observação da estrela T CrB"""
    
    AAVSO_URL = "https://apps.aavso.org/webobs/results/?star=t+crb&num_results=20&obs_types=all&page=1"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
    
    def fetch_latest_observation(self) -> Optional[Dict]:
        """
        Busca a observação mais recente da estrela T CrB
        
        Returns:
            Dict com os dados da observação ou None se houver erro
        """
        try:
            print(f"Buscando dados de {self.AAVSO_URL}...")
            response = self.session.get(self.AAVSO_URL, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Encontra a tabela de observações
            table = soup.find('table', class_='observations')
            if not table:
                raise ValueError("Tabela de observações não encontrada")
            
            # Encontra o tbody
            tbody = table.find('tbody')
            if not tbody:
                raise ValueError("Tbody não encontrado")
            
            # Encontra a primeira linha com classe 'obs'
            first_row = tbody.find('tr', class_='obs')
            if not first_row:
                raise ValueError("Nenhuma observação encontrada")
            
            # Extrai as células
            cells = first_row.find_all('td')
            
            # A tabela tem 3 colunas vazias no início (colspan="3")
            # Então os dados começam no índice 1
            # Extrai calendar_date original
            calendar_date_original = cells[3].get_text(strip=True)
            
            # Converte para formato brasileiro
            calendar_date_formatted = parse_calendar_date(calendar_date_original)
            
            # Formata a data de coleta no formato brasileiro
            scraped_at = datetime.now().strftime('%d/%m/%Y %H:%M')
            
            data = {
                'star': cells[1].get_text(strip=True),
                'jd': cells[2].get_text(strip=True),
                'calendar_date': calendar_date_formatted,  # Usa a data formatada
                'magnitude': cells[4].get_text(strip=True),
                'error': cells[5].get_text(strip=True),
                'filter': cells[6].get_text(strip=True),
                'observer': cells[7].get_text(strip=True),
                'scraped_at': scraped_at
            }
            
            print(f"✓ Dados extraídos: {data['star']} - Magnitude: {data['magnitude']}")
            return data
            
        except requests.RequestException as e:
            print(f"✗ Erro na requisição HTTP: {e}")
            return None
        except (ValueError, IndexError, AttributeError) as e:
            print(f"✗ Erro ao parsear HTML: {e}")
            return None
        except Exception as e:
            print(f"✗ Erro inesperado: {e}")
            return None


def main():
    """Função principal para teste"""
    scraper = TCrbScraper()
    data = scraper.fetch_latest_observation()
    
    if data:
        print("\n=== Dados Coletados ===")
        for key, value in data.items():
            print(f"{key:15}: {value}")
    else:
        print("\n✗ Falha ao coletar dados")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())