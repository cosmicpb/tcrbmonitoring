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


async def scrape_page(page_num):
    """
    Faz scraping de uma página específica do AAVSO
    Retorna uma lista de observações da página
    """
    AAVSO_URL = f"https://apps.aavso.org/webobs/results/?star=t+crb&num_results=20&obs_types=all&page={page_num}"
    
    try:
        print(f"[SCRAPER] Coletando página {page_num}...")
        response = await fetch(AAVSO_URL)
        html = await response.text()
        
        print(f"[SCRAPER] HTML recebido: {len(html)} caracteres")
        
        # Parse HTML
        if '<table class="observations">' in html:
            table_start = html.find('<table class="observations">')
            print(f"[SCRAPER] Encontrou: <table class=\"observations\">")
        elif '<table id="results"' in html:
            table_start = html.find('<table id="results"')
            print(f"[SCRAPER] Encontrou: <table id=\"results\">")
        elif '<table' in html:
            table_start = html.find('<table')
            print(f"[SCRAPER] Encontrou: <table>")
        else:
            print(f"[SCRAPER] ❌ NENHUMA TABELA ENCONTRADA!")
            print(f"[SCRAPER] Primeiros 500 chars: {html[:500]}")
            raise ValueError("Nenhuma tabela encontrada no HTML")
        
        if table_start == -1:
            raise ValueError("Tabela não encontrada")
        
        # IMPORTANTE: Procurar TODAS as linhas de observação no HTML completo
        # não apenas no tbody, pois o AAVSO pode ter múltiplas linhas fora do tbody
        print(f"[SCRAPER] Procurando todas as linhas <tr class='obs tr-even'> e <tr class='obs tr-odd'>")
        
        # Coleta TODAS as linhas de observação
        observations = []
        pos = table_start
        scraped_at = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        # Conta quantas linhas <tr class='obs existem
        tr_even_count = html.count("<tr class='obs tr-even'", table_start)
        tr_odd_count = html.count("<tr class='obs tr-odd'", table_start)
        total_obs_rows = tr_even_count + tr_odd_count
        print(f"[SCRAPER] Linhas de observação encontradas: {total_obs_rows} (even: {tr_even_count}, odd: {tr_odd_count})")
        
        row_num = 0
        while True:
            # Procura próxima linha de observação (tr-even ou tr-odd)
            row_start_even = html.find("<tr class='obs tr-even'", pos)
            row_start_odd = html.find("<tr class='obs tr-odd'", pos)
            
            # Pega a que vier primeiro
            if row_start_even == -1 and row_start_odd == -1:
                break
            elif row_start_even == -1:
                row_start = row_start_odd
            elif row_start_odd == -1:
                row_start = row_start_even
            else:
                row_start = min(row_start_even, row_start_odd)
            
            row_end = html.find('</tr>', row_start)
            if row_end == -1:
                break
                
            row = html[row_start:row_end]
            row_num += 1
            
            print(f"[SCRAPER] Processando linha {row_num}: {len(row)} chars")
            
            # Pula linhas de detalhes (obs-detail-tr)
            # IMPORTANTE: Só pular se for REALMENTE uma linha de detalhes
            if 'obs-detail-tr' in row:
                print(f"[SCRAPER] Linha {row_num}: PULADA (obs-detail-tr)")
                pos = row_end + 5
                continue
            
            # Extrai células
            cells = []
            cell_pos = 0
            while True:
                td_start = row.find('<td', cell_pos)
                if td_start == -1:
                    break
                td_end = row.find('</td>', td_start)
                cell_content = row[td_start:td_end + 5]
                
                text_start = cell_content.find('>')
                text = cell_content[text_start + 1:].replace('</td>', '')
                
                # Remove tags HTML
                while '<' in text:
                    tag_start = text.find('<')
                    tag_end = text.find('>', tag_start)
                    if tag_end == -1:
                        break
                    text = text[:tag_start] + text[tag_end + 1:]
                
                cells.append(text.strip())
                cell_pos = td_end + 5
            
            # Remove células vazias do início
            non_empty_cells = [cell for cell in cells if cell]
            
            print(f"[SCRAPER] Linha {row_num}: {len(cells)} células totais, {len(non_empty_cells)} não-vazias")
            if non_empty_cells:
                print(f"[SCRAPER] Primeiras células: {non_empty_cells[:3]}")
            
            # Valida número mínimo de células
            if len(non_empty_cells) < 7:
                print(f"[SCRAPER] Linha {row_num}: PULADA (menos de 7 células)")
                pos = row_end + 5
                continue
            
            calendar_date_original = non_empty_cells[2]
            calendar_date_formatted = parse_calendar_date(calendar_date_original)
            
            # Remove "Details..." do observer se presente
            observer = non_empty_cells[6]
            if 'Details' in observer:
                observer = observer.split('Details')[0].strip()
            
            data = {
                'star': non_empty_cells[0],
                'jd': non_empty_cells[1],
                'calendar_date': calendar_date_formatted,
                'magnitude': non_empty_cells[3],
                'error': non_empty_cells[4],
                'filter': non_empty_cells[5],
                'observer': observer,
                'scraped_at': scraped_at
            }
            
            observations.append(data)
            pos = row_end + 5
        
        print(f"[SCRAPER] Página {page_num}: {len(observations)} observações")
        return observations
        
    except Exception as e:
        print(f"[SCRAPER] Erro na página {page_num}: {str(e)}")
        return []


async def scrape_latest_observations():
    """
    Faz scraping das primeiras 15 páginas do AAVSO (300 observações)
    para garantir que não perca dados entre execuções do cron
    Retorna uma lista consolidada de todas as observações
    """
    all_observations = []
    
    try:
        print(f"[SCRAPER] Iniciando coleta das primeiras 15 páginas...")
        
        # Coleta páginas 1 a 15 (300 observações)
        # Isso garante que mesmo com alta frequência de observações,
        # não perderemos dados entre as execuções horárias do cron
        for page in range(1, 16):
            page_observations = await scrape_page(page)
            all_observations.extend(page_observations)
            
            # Se uma página retornar vazia, para de coletar
            if not page_observations:
                print(f"[SCRAPER] Página {page} vazia, parando coleta")
                break
        
        print(f"[SCRAPER] ========================================")
        print(f"[SCRAPER] Total de observações coletadas: {len(all_observations)}")
        if all_observations:
            print(f"[SCRAPER] Primeira: JD {all_observations[0]['jd']}, Mag {all_observations[0]['magnitude']}")
            print(f"[SCRAPER] Última: JD {all_observations[-1]['jd']}, Mag {all_observations[-1]['magnitude']}")
        print(f"[SCRAPER] ========================================")
        
        return all_observations
        
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
        
        # Converte jd para float para jd_numeric
        try:
            jd_numeric = float(data['jd'])
        except (ValueError, TypeError):
            print(f"[SCRAPER] ⚠️  Erro ao converter JD para float: {data['jd']}")
            jd_numeric = None
        
        # Insere nova observação (incluindo jd_numeric)
        insert_query = """
        INSERT INTO observations (star, jd, jd_numeric, calendar_date, magnitude, error, filter, observer, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        await env.DB.prepare(insert_query).bind(
            data['star'],
            data['jd'],
            jd_numeric,
            data['calendar_date'],
            data['magnitude'],
            data['error'],
            data['filter'],
            data['observer'],
            data['scraped_at']
        ).run()
        
        print(f"[SCRAPER] ✅ Nova observação salva no D1 (JD: {data['jd']}, jd_numeric: {jd_numeric})")
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
        
        # Faz scraping de TODAS as observações da página 1
        observations = await scrape_latest_observations()
        
        if not observations:
            print("[SCRAPER] ⚠️  Nenhuma observação coletada")
            return
        
        # Salva cada observação no D1
        if hasattr(env, 'DB'):
            saved_count = 0
            duplicate_count = 0
            error_count = 0
            
            for data in observations:
                result = await save_to_d1(env, data)
                if result['status'] == 'saved':
                    saved_count += 1
                elif result['status'] == 'duplicate':
                    duplicate_count += 1
                else:
                    error_count += 1
            
            print(f"[SCRAPER] ========================================")
            print(f"[SCRAPER] Resumo da coleta:")
            print(f"[SCRAPER]   Total coletado: {len(observations)}")
            print(f"[SCRAPER]   ✅ Novas: {saved_count}")
            print(f"[SCRAPER]   ⏭️  Duplicadas: {duplicate_count}")
            print(f"[SCRAPER]   ❌ Erros: {error_count}")
            print(f"[SCRAPER] ========================================")
        else:
            print("[SCRAPER] ⚠️  D1 Database não configurado")
        
        print(f"[SCRAPER] Coleta concluída com sucesso")
        
    except Exception as e:
        print(f"[SCRAPER] ❌ ERRO durante coleta: {str(e)}")
        raise