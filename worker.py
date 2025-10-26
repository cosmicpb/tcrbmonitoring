"""
Cloudflare Worker em Python para monitoramento T CrB
Executa via Cron Triggers a cada hora
"""

from js import Response, fetch
import json
from datetime import datetime


async def scrape_latest_observation():
    """
    Faz scraping dos dados mais recentes da estrela T CrB
    """
    AAVSO_URL = "https://apps.aavso.org/webobs/results/?star=t+crb&num_results=20&obs_types=all&page=1"
    
    try:
        # Faz requisição HTTP
        response = await fetch(AAVSO_URL)
        html = await response.text()
        
        # Parse HTML simples (sem BeautifulSoup no Workers)
        # Procura pela tabela de observações
        table_start = html.find('<table class="observations">')
        if table_start == -1:
            raise ValueError("Tabela não encontrada")
        
        tbody_start = html.find('<tbody>', table_start)
        tbody_end = html.find('</tbody>', tbody_start)
        tbody = html[tbody_start:tbody_end]
        
        # Procura primeira linha com classe "obs"
        row_start = tbody.find('<tr class="obs')
        if row_start == -1:
            raise ValueError("Nenhuma observação encontrada")
        
        row_end = tbody.find('</tr>', row_start)
        row = tbody[row_start:row_end]
        
        # Extrai células <td>
        cells = []
        pos = 0
        while True:
            td_start = row.find('<td', pos)
            if td_start == -1:
                break
            td_end = row.find('</td>', td_start)
            cell_content = row[td_start:td_end + 5]
            
            # Remove tags HTML
            text_start = cell_content.find('>')
            text = cell_content[text_start + 1:].replace('</td>', '')
            # Remove tags internas
            while '<' in text:
                tag_start = text.find('<')
                tag_end = text.find('>', tag_start)
                if tag_end == -1:
                    break
                text = text[:tag_start] + text[tag_end + 1:]
            
            cells.append(text.strip())
            pos = td_end + 5
        
        # Formata a data de coleta no formato brasileiro
        scraped_at = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        # Extrai dados (índices ajustados para as 3 colunas vazias)
        data = {
            'star': cells[1] if len(cells) > 1 else '',
            'jd': cells[2] if len(cells) > 2 else '',
            'calendar_date': cells[3] if len(cells) > 3 else '',
            'magnitude': cells[4] if len(cells) > 4 else '',
            'error': cells[5] if len(cells) > 5 else '',
            'filter': cells[6] if len(cells) > 6 else '',
            'observer': cells[7] if len(cells) > 7 else '',
            'scraped_at': scraped_at
        }
        
        return data
        
    except Exception as e:
        raise Exception(f"Erro ao fazer scraping: {str(e)}")


async def save_to_d1(env, data):
    """
    Salva dados no D1 Database
    """
    try:
        # Verifica se já existe
        check_query = "SELECT COUNT(*) as count FROM observations WHERE jd = ?"
        result = await env.DB.prepare(check_query).bind(data['jd']).first()
        
        if result and result['count'] > 0:
            return {'status': 'duplicate', 'message': 'Observação já existe'}
        
        # Insere nova observação
        insert_query = """
        INSERT INTO observations (star, jd, calendar_date, magnitude, error, filter, observer, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        await env.DB.prepare(insert_query).bind(
            data['star'],
            data['jd'],
            data['calendar_date'],
            data['magnitude'],
            data['error'],
            data['filter'],
            data['observer'],
            data['scraped_at']
        ).run()
        
        return {'status': 'saved', 'message': 'Nova observação salva'}
        
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


async def on_scheduled(event, env, ctx):
    """
    Handler para Cron Triggers
    Executado automaticamente a cada hora
    """
    try:
        print(f"[{datetime.utcnow().isoformat()}] Iniciando coleta...")
        
        # Faz scraping
        data = await scrape_latest_observation()
        print(f"Dados coletados: {data['star']} - Magnitude: {data['magnitude']}")
        
        # Salva no D1
        if hasattr(env, 'DB'):
            result = await save_to_d1(env, data)
            print(f"Resultado DB: {result['status']} - {result['message']}")
        else:
            print("AVISO: D1 Database não configurado")
        
        print("Coleta concluída com sucesso")
        
    except Exception as e:
        print(f"ERRO durante coleta: {str(e)}")
        raise