"""
Cloudflare Worker - Scraper T CrB
Executa via Cron Trigger a cada hora
Responsável apenas por coletar dados do AAVSO e salvar no D1
"""

from js import fetch
from datetime import datetime


def parse_calendar_date(calendar_date):
    """
    Converte data do formato AAVSO para dd/MM/YYYY HH:mm
    Exemplo: "2025 Oct. 26.07083" -> "26/10/2025 01:42"
    """
    try:
        parts = calendar_date.split()
        year = parts[0]
        month_str = parts[1].replace('.', '')
        day_decimal = parts[2]
        
        months = {
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
            'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
        }
        month = months.get(month_str, '01')
        
        day_parts = day_decimal.split('.')
        day = day_parts[0].zfill(2)
        
        if len(day_parts) > 1:
            fraction = float('0.' + day_parts[1])
            hours = int(fraction * 24)
            minutes = int((fraction * 24 - hours) * 60)
        else:
            hours = 0
            minutes = 0
        
        return f"{day}/{month}/{year} {hours:02d}:{minutes:02d}"
    except:
        return calendar_date


async def scrape_latest_observation():
    """
    Faz scraping dos dados mais recentes da estrela T CrB
    """
    AAVSO_URL = "https://apps.aavso.org/webobs/results/?star=t+crb&num_results=20&obs_types=all&page=1"
    
    try:
        print(f"[SCRAPER] Fazendo requisição para: {AAVSO_URL}")
        response = await fetch(AAVSO_URL)
        html = await response.text()
        print(f"[SCRAPER] Status: {response.status}, Tamanho: {len(html)} caracteres")
        
        # Parse HTML
        if '<table class="observations">' in html:
            table_start = html.find('<table class="observations">')
        elif '<table id="results"' in html:
            table_start = html.find('<table id="results"')
        elif '<table' in html:
            table_start = html.find('<table')
        else:
            raise ValueError("Nenhuma tabela encontrada no HTML")
        
        if table_start == -1:
            raise ValueError("Tabela não encontrada")
        
        tbody_start = html.find('<tbody>', table_start)
        tbody_end = html.find('</tbody>', tbody_start)
        tbody = html[tbody_start:tbody_end]
        
        # Procura primeira linha
        row_start = tbody.find('<tr class="obs')
        if row_start == -1:
            row_start = tbody.find('<tr')
            if row_start == -1:
                raise ValueError("Nenhuma observação encontrada")
        
        row_end = tbody.find('</tr>', row_start)
        row = tbody[row_start:row_end]
        
        # Extrai células
        cells = []
        pos = 0
        while True:
            td_start = row.find('<td', pos)
            if td_start == -1:
                break
            td_end = row.find('</td>', td_start)
            cell_content = row[td_start:td_end + 5]
            
            text_start = cell_content.find('>')
            text = cell_content[text_start + 1:].replace('</td>', '')
            
            while '<' in text:
                tag_start = text.find('<')
                tag_end = text.find('>', tag_start)
                if tag_end == -1:
                    break
                text = text[:tag_start] + text[tag_end + 1:]
            
            cells.append(text.strip())
            pos = td_end + 5
        
        scraped_at = datetime.now().strftime('%d/%m/%Y %H:%M')
        calendar_date_original = cells[3] if len(cells) > 3 else ''
        calendar_date_formatted = parse_calendar_date(calendar_date_original)
        
        data = {
            'star': cells[1] if len(cells) > 1 else '',
            'jd': cells[2] if len(cells) > 2 else '',
            'calendar_date': calendar_date_formatted,
            'magnitude': cells[4] if len(cells) > 4 else '',
            'error': cells[5] if len(cells) > 5 else '',
            'filter': cells[6] if len(cells) > 6 else '',
            'observer': cells[7] if len(cells) > 7 else '',
            'scraped_at': scraped_at
        }
        
        print(f"[SCRAPER] Dados coletados: {data['star']} - Mag: {data['magnitude']} - Filtro: {data['filter']}")
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
        
        if result:
            count = result.count if hasattr(result, 'count') else 0
            if count > 0:
                print(f"[SCRAPER] Observação já existe (JD: {data['jd']})")
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
        
        print(f"[SCRAPER] ✅ Nova observação salva no D1")
        return {'status': 'saved', 'message': 'Nova observação salva'}
        
    except Exception as e:
        print(f"[SCRAPER] ❌ Erro ao salvar no D1: {str(e)}")
        return {'status': 'error', 'message': str(e)}


async def on_scheduled(event, env, ctx):
    """
    Handler para Cron Triggers
    Executado automaticamente a cada hora
    """
    try:
        print(f"[SCRAPER] ========================================")
        print(f"[SCRAPER] Iniciando coleta: {datetime.utcnow().isoformat()}")
        print(f"[SCRAPER] ========================================")
        
        # Faz scraping
        data = await scrape_latest_observation()
        
        # Salva no D1
        if hasattr(env, 'DB'):
            result = await save_to_d1(env, data)
            print(f"[SCRAPER] Resultado: {result['status']} - {result['message']}")
        else:
            print("[SCRAPER] ⚠️  D1 Database não configurado")
        
        print(f"[SCRAPER] ========================================")
        print(f"[SCRAPER] Coleta concluída com sucesso")
        print(f"[SCRAPER] ========================================")
        
    except Exception as e:
        print(f"[SCRAPER] ❌ ERRO durante coleta: {str(e)}")
        raise