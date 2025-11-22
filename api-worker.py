"""
Cloudflare Worker - API T CrB
Serve dados via endpoints REST com rate limiting e segurança
Responsável apenas por fornecer acesso aos dados do D1
"""

import json
import time
from js import Response, URL, Headers

# Configurações de Rate Limiting
RATE_LIMIT_WINDOW = 60  # 60 segundos
RATE_LIMIT_MAX_REQUESTS = 100  # 100 requisições por minuto por IP
RATE_LIMIT_ENABLED = True  # Ativar/desativar rate limiting

# Configurações de Cache
CACHE_TTL_STATS = 300  # 5 minutos para /stats
CACHE_TTL_LATEST = 60  # 1 minuto para /latest
CACHE_TTL_OBSERVATIONS = 30  # 30 segundos para /observations


def get_client_ip(request):
    """Extrai IP do cliente da requisição"""
    # Cloudflare adiciona o IP real no header CF-Connecting-IP
    headers = request.headers
    if headers.has('CF-Connecting-IP'):
        return headers.get('CF-Connecting-IP')
    elif headers.has('X-Forwarded-For'):
        return headers.get('X-Forwarded-For').split(',')[0].strip()
    return 'unknown'


def json_response(data, status=200, cache_ttl=None):
    """Helper para criar Response JSON com CORS e cache"""
    headers = Headers.new()
    headers.set("Content-Type", "application/json")
    
    # CORS headers
    headers.set("Access-Control-Allow-Origin", "*")
    headers.set("Access-Control-Allow-Methods", "GET, OPTIONS")
    headers.set("Access-Control-Allow-Headers", "Content-Type")
    
    # Cache headers
    if cache_ttl and cache_ttl > 0:
        headers.set("Cache-Control", f"public, max-age={cache_ttl}")
    else:
        headers.set("Cache-Control", "no-cache, no-store, must-revalidate")
    
    # Security headers
    headers.set("X-Content-Type-Options", "nosniff")
    headers.set("X-Frame-Options", "DENY")
    headers.set("X-XSS-Protection", "1; mode=block")
    
    return Response.new(json.dumps(data), status=status, headers=headers)


async def check_rate_limit(request, env):
    """
    Verifica rate limit usando KV (se disponível) ou memória
    Retorna (allowed: bool, remaining: int, reset_time: int)
    """
    if not RATE_LIMIT_ENABLED:
        return True, RATE_LIMIT_MAX_REQUESTS, 0
    
    client_ip = get_client_ip(request)
    current_time = int(time.time())
    window_start = current_time - (current_time % RATE_LIMIT_WINDOW)
    key = f"ratelimit:{client_ip}:{window_start}"
    
    # Se KV estiver disponível, usa KV para rate limiting
    if hasattr(env, 'RATE_LIMIT_KV'):
        try:
            value = await env.RATE_LIMIT_KV.get(key)
            count = int(value) if value else 0
            
            if count >= RATE_LIMIT_MAX_REQUESTS:
                reset_time = window_start + RATE_LIMIT_WINDOW
                return False, 0, reset_time
            
            # Incrementa contador
            await env.RATE_LIMIT_KV.put(key, str(count + 1), expirationTtl=RATE_LIMIT_WINDOW)
            remaining = RATE_LIMIT_MAX_REQUESTS - count - 1
            reset_time = window_start + RATE_LIMIT_WINDOW
            return True, remaining, reset_time
            
        except Exception as e:
            print(f"[RATE_LIMIT] Erro ao usar KV: {e}")
            # Se falhar, permite a requisição
            return True, RATE_LIMIT_MAX_REQUESTS, 0
    
    # Se KV não estiver disponível, permite todas as requisições
    # (rate limiting será feito pelo Cloudflare automaticamente)
    return True, RATE_LIMIT_MAX_REQUESTS, 0


def validate_pagination_params(page, limit):
    """Valida e sanitiza parâmetros de paginação"""
    try:
        page = int(page) if page else 1
        limit = int(limit) if limit else 50
    except (ValueError, TypeError):
        return 1, 50, "Invalid pagination parameters"
    
    # Validações
    if page < 1:
        return 1, 50, "Page must be >= 1"
    if limit < 1 or limit > 1000:
        return page, 50, "Limit must be between 1 and 1000"
    
    return page, limit, None


async def on_fetch(request, env, ctx):
    """
    Handler para requisições HTTP com rate limiting e segurança
    Endpoints REST para consultar dados do D1
    """
    try:
        # Handle CORS preflight
        if request.method == 'OPTIONS':
            return json_response({'status': 'ok'}, status=200)
        
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
        
        client_ip = get_client_ip(request)
        print(f"[API] {client_ip} -> {request.method} {pathname} | Params: {params}")
        
        # Rate limiting
        allowed, remaining, reset_time = await check_rate_limit(request, env)
        if not allowed:
            print(f"[API] ⚠️  Rate limit exceeded for {client_ip}")
            return json_response({
                'status': 'error',
                'message': 'Rate limit exceeded',
                'retry_after': reset_time - int(time.time())
            }, status=429)
        
        # Log rate limit info
        if remaining < 10:
            print(f"[API] ⚠️  {client_ip} has {remaining} requests remaining")
        
        # Verifica se DB está disponível
        if not hasattr(env, 'DB'):
            return json_response({
                'status': 'error',
                'message': 'D1 Database não configurado'
            }, status=500)
        
        # Rota: /observations (com paginação)
        if pathname == '/observations':
            # Valida parâmetros de paginação
            page, limit, error = validate_pagination_params(
                params.get('page'),
                params.get('limit')
            )
            
            if error:
                return json_response({
                    'status': 'error',
                    'message': error
                }, status=400)
            
            # Calcula offset
            offset = (page - 1) * limit
            
            print(f"[API] Consultando página {page} com {limit} observações (offset: {offset})...")
            
            # Filtro opcional por estrela (default T CrB)
            star_param = params.get('star')
            normalized_star = (star_param or 'T CrB').replace(' ', '').lower()
            where_clause = "WHERE REPLACE(LOWER(star), ' ', '') = ?"

            # Query com paginação - ordenado por Julian Date (ordem cronológica astronômica)
            query = f"SELECT * FROM observations {where_clause} ORDER BY CAST(jd AS REAL) DESC LIMIT {limit} OFFSET {offset}"
            result = await env.DB.prepare(query).bind(normalized_star).all()
            
            # Total de registros
            count_query = f"SELECT COUNT(*) as total FROM observations {where_clause}"
            count_result = await env.DB.prepare(count_query).bind(normalized_star).first()
            
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
            total_pages = (total + limit - 1) // limit  # Arredonda para cima
            
            print(f"[API] Retornando {len(observations)} de {total} observações (página {page}/{total_pages})")
            
            response_data = {
                'status': 'success',
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total_pages': total_pages,
                    'total_records': total,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                },
                'observations': observations,
                'rate_limit': {
                    'remaining': remaining,
                    'reset': reset_time
                }
            }
            
            return json_response(response_data, cache_ttl=CACHE_TTL_OBSERVATIONS)
        
        # Rota: /latest
        elif pathname == '/latest':
            print(f"[API] Consultando última observação...")
            
            # Filtro por estrela (default T CrB)
            star_param = params.get('star') if 'params' in locals() else None
            normalized_star = (star_param or 'T CrB').replace(' ', '').lower()
            where_clause = "WHERE REPLACE(LOWER(star), ' ', '') = ?"

            # Ordenado por Julian Date (última observação astronômica)
            query = f"SELECT * FROM observations {where_clause} ORDER BY CAST(jd AS REAL) DESC LIMIT 1"
            result = await env.DB.prepare(query).bind(normalized_star).first()
            
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
                    'observation': observation,
                    'rate_limit': {
                        'remaining': remaining,
                        'reset': reset_time
                    }
                }, cache_ttl=CACHE_TTL_LATEST)
            else:
                return json_response({
                    'status': 'success',
                    'message': 'Nenhuma observação encontrada'
                })
        
        # Rota: /stats
        elif pathname == '/stats':
            print(f"[API] Consultando estatísticas...")
            
            # Filtro por estrela (default T CrB)
            star_param = params.get('star') if 'params' in locals() else None
            normalized_star = (star_param or 'T CrB').replace(' ', '').lower()
            where_clause = "WHERE REPLACE(LOWER(star), ' ', '') = ?"

            count_query = f"SELECT COUNT(*) as total FROM observations {where_clause}"
            count_result = await env.DB.prepare(count_query).bind(normalized_star).first()
            
            # Última observação por Julian Date (ordem cronológica astronômica)
            latest_query = f"SELECT calendar_date, magnitude FROM observations {where_clause} ORDER BY CAST(jd AS REAL) DESC LIMIT 1"
            latest_result = await env.DB.prepare(latest_query).bind(normalized_star).first()
            
            stats_query = """
                SELECT
                    MIN(CAST(magnitude AS REAL)) as min_mag,
                    MAX(CAST(magnitude AS REAL)) as max_mag,
                    AVG(CAST(magnitude AS REAL)) as avg_mag
                FROM observations
                WHERE REPLACE(LOWER(star), ' ', '') = ?
                  AND magnitude != ''
            """
            stats_result = await env.DB.prepare(stats_query).bind(normalized_star).first()
            
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
                },
                'rate_limit': {
                    'remaining': remaining,
                    'reset': reset_time
                }
            }, cache_ttl=CACHE_TTL_STATS)
        
        # Rota padrão: informações da API
        else:
            count_query = "SELECT COUNT(*) as total FROM observations"
            count_result = await env.DB.prepare(count_query).first()
            total = count_result.total if count_result and hasattr(count_result, 'total') else 0
            
            print(f"[API] Info da API - Total: {total} observações")
            
            return json_response({
                'status': 'online',
                'name': 'T CrB Monitoring API',
                'version': '2.1',
                'total_observations': total,
                'endpoints': {
                    'GET /': 'Informações da API',
                    'GET /observations?page=X&limit=Y&star=T%20CrB': 'Observações paginadas por estrela (padrão: T CrB; máx limit: 1000)',
                    'GET /latest?star=T%20CrB': 'Última observação por estrela',
                    'GET /stats?star=T%20CrB': 'Estatísticas por estrela'
                },
                'rate_limiting': {
                    'enabled': RATE_LIMIT_ENABLED,
                    'max_requests': RATE_LIMIT_MAX_REQUESTS,
                    'window_seconds': RATE_LIMIT_WINDOW,
                    'current_remaining': remaining,
                    'reset_at': reset_time
                },
                'info': 'Dados coletados automaticamente a cada hora pelo Scraper Worker'
            }, cache_ttl=60)
        
    except Exception as e:
        print(f"[API] ❌ Erro: {str(e)}")
        return json_response({
            'status': 'error',
            'message': str(e)
        }, status=500)