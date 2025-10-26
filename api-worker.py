"""
Cloudflare Worker - API T CrB
Serve dados via endpoints REST
Responsável apenas por fornecer acesso aos dados do D1
"""

import json
from js import Response, URL, Headers


def json_response(data, status=200):
    """Helper para criar Response JSON corretamente"""
    headers = Headers.new()
    headers.set("Content-Type", "application/json")
    return Response.new(json.dumps(data), status=status, headers=headers)


async def on_fetch(request, env, ctx):
    """
    Handler para requisições HTTP
    Endpoints REST para consultar dados do D1
    """
    try:
        # Parse URL usando o objeto URL do JavaScript
        url_obj = URL.new(request.url)
        pathname = url_obj.pathname
        
        # Remove trailing slash
        if pathname.endswith('/') and len(pathname) > 1:
            pathname = pathname[:-1]
        
        # Extrai parâmetros da query string
        params = {}
        search_params = url_obj.searchParams
        if search_params:
            # Itera sobre os parâmetros
            keys = search_params.keys()
            for key in keys:
                params[key] = search_params.get(key)
        
        print(f"[API] Request: {pathname} | Params: {params}")
        
        # Verifica se DB está disponível
        if not hasattr(env, 'DB'):
            return json_response({
                'status': 'error',
                'message': 'D1 Database não configurado'
            }, status=500)
        
        # Rota: /observations
        if pathname == '/observations':
            limit = int(params.get('limit', '10'))
            limit = max(1, min(limit, 100))  # Entre 1 e 100
            
            print(f"[API] Consultando {limit} observações...")
            
            query = f"SELECT * FROM observations ORDER BY created_at DESC LIMIT {limit}"
            result = await env.DB.prepare(query).all()
            
            count_query = "SELECT COUNT(*) as total FROM observations"
            count_result = await env.DB.prepare(count_query).first()
            
            # Converte resultados
            observations = []
            if result and hasattr(result, 'results'):
                for obs in result.results:
                    observations.append({
                        'id': obs.id if hasattr(obs, 'id') else None,
                        'star': obs.star if hasattr(obs, 'star') else None,
                        'jd': obs.jd if hasattr(obs, 'jd') else None,
                        'calendar_date': obs.calendar_date if hasattr(obs, 'calendar_date') else None,
                        'magnitude': obs.magnitude if hasattr(obs, 'magnitude') else None,
                        'error': obs.error if hasattr(obs, 'error') else None,
                        'filter': obs.filter if hasattr(obs, 'filter') else None,
                        'observer': obs.observer if hasattr(obs, 'observer') else None,
                        'scraped_at': obs.scraped_at if hasattr(obs, 'scraped_at') else None,
                        'created_at': obs.created_at if hasattr(obs, 'created_at') else None
                    })
            
            total = count_result.total if count_result and hasattr(count_result, 'total') else 0
            
            print(f"[API] Retornando {len(observations)} de {total} observações")
            
            return json_response({
                'status': 'success',
                'total_observations': total,
                'returned': len(observations),
                'limit': limit,
                'observations': observations
            })
        
        # Rota: /latest
        elif pathname == '/latest':
            print(f"[API] Consultando última observação...")
            
            query = "SELECT * FROM observations ORDER BY created_at DESC LIMIT 1"
            result = await env.DB.prepare(query).first()
            
            if result:
                observation = {
                    'id': result.id if hasattr(result, 'id') else None,
                    'star': result.star if hasattr(result, 'star') else None,
                    'jd': result.jd if hasattr(result, 'jd') else None,
                    'calendar_date': result.calendar_date if hasattr(result, 'calendar_date') else None,
                    'magnitude': result.magnitude if hasattr(result, 'magnitude') else None,
                    'error': result.error if hasattr(result, 'error') else None,
                    'filter': result.filter if hasattr(result, 'filter') else None,
                    'observer': result.observer if hasattr(result, 'observer') else None,
                    'scraped_at': result.scraped_at if hasattr(result, 'scraped_at') else None,
                    'created_at': result.created_at if hasattr(result, 'created_at') else None
                }
                
                print(f"[API] Última observação: {observation['star']} - Mag: {observation['magnitude']}")
                
                return json_response({
                    'status': 'success',
                    'observation': observation
                })
            else:
                return json_response({
                    'status': 'success',
                    'message': 'Nenhuma observação encontrada'
                })
        
        # Rota: /stats
        elif pathname == '/stats':
            print(f"[API] Consultando estatísticas...")
            
            count_query = "SELECT COUNT(*) as total FROM observations"
            count_result = await env.DB.prepare(count_query).first()
            
            latest_query = "SELECT calendar_date, magnitude FROM observations ORDER BY created_at DESC LIMIT 1"
            latest_result = await env.DB.prepare(latest_query).first()
            
            stats_query = """
                SELECT 
                    MIN(CAST(magnitude AS REAL)) as min_mag,
                    MAX(CAST(magnitude AS REAL)) as max_mag,
                    AVG(CAST(magnitude AS REAL)) as avg_mag
                FROM observations
                WHERE magnitude != ''
            """
            stats_result = await env.DB.prepare(stats_query).first()
            
            total = count_result.total if count_result and hasattr(count_result, 'total') else 0
            latest_date = latest_result.calendar_date if latest_result and hasattr(latest_result, 'calendar_date') else None
            latest_mag = latest_result.magnitude if latest_result and hasattr(latest_result, 'magnitude') else None
            
            min_mag = stats_result.min_mag if stats_result and hasattr(stats_result, 'min_mag') else None
            max_mag = stats_result.max_mag if stats_result and hasattr(stats_result, 'max_mag') else None
            avg_mag = stats_result.avg_mag if stats_result and hasattr(stats_result, 'avg_mag') else None
            
            print(f"[API] Estatísticas: {total} obs, Mag média: {avg_mag}")
            
            return json_response({
                'status': 'success',
                'statistics': {
                    'total_observations': total,
                    'latest_observation': {
                        'date': latest_date,
                        'magnitude': latest_mag
                    },
                    'magnitude_stats': {
                        'min': min_mag,
                        'max': max_mag,
                        'average': avg_mag
                    }
                }
            })
        
        # Rota padrão: informações da API
        else:
            count_query = "SELECT COUNT(*) as total FROM observations"
            count_result = await env.DB.prepare(count_query).first()
            total = count_result.total if count_result and hasattr(count_result, 'total') else 0
            
            print(f"[API] Info da API - Total: {total} observações")
            
            return json_response({
                'status': 'online',
                'name': 'T CrB Monitoring API',
                'version': '2.0',
                'total_observations': total,
                'endpoints': {
                    'GET /': 'Informações da API',
                    'GET /observations?limit=X': 'Últimas X observações (padrão: 10, máx: 100)',
                    'GET /latest': 'Última observação coletada',
                    'GET /stats': 'Estatísticas gerais'
                },
                'info': 'Dados coletados automaticamente a cada hora pelo Scraper Worker'
            })
        
    except Exception as e:
        print(f"[API] ❌ Erro: {str(e)}")
        return json_response({
            'status': 'error',
            'message': str(e)
        }, status=500)