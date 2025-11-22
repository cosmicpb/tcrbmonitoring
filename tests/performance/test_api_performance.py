#!/usr/bin/env python3
"""
Script de Análise de Performance da API T CrB
Testa diferentes endpoints e cargas para mapear performance
"""

import requests
import time
import statistics
from datetime import datetime
from typing import Dict, List, Tuple

API_BASE_URL = "https://tcrb-api.pbaldacimjr.workers.dev"

class APIPerformanceTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = []
        
    def test_endpoint(self, endpoint: str, params: Dict = None, iterations: int = 10) -> Dict:
        """Testa um endpoint múltiplas vezes e coleta métricas"""
        print(f"\n{'='*60}")
        print(f"Testando: {endpoint}")
        print(f"Parâmetros: {params}")
        print(f"Iterações: {iterations}")
        print(f"{'='*60}")
        
        response_times = []
        status_codes = []
        data_sizes = []
        errors = []
        
        for i in range(iterations):
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=30)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # em ms
                response_times.append(response_time)
                status_codes.append(response.status_code)
                
                if response.status_code == 200:
                    data_sizes.append(len(response.content))
                    print(f"  [{i+1}/{iterations}] ✅ {response_time:.2f}ms | {len(response.content)} bytes")
                else:
                    print(f"  [{i+1}/{iterations}] ❌ Status {response.status_code} | {response_time:.2f}ms")
                    errors.append(f"Status {response.status_code}")
                
                # Pequeno delay entre requisições
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  [{i+1}/{iterations}] ❌ Erro: {str(e)}")
                errors.append(str(e))
        
        # Calcula estatísticas
        if response_times:
            stats = {
                'endpoint': endpoint,
                'params': params,
                'iterations': iterations,
                'successful_requests': len([s for s in status_codes if s == 200]),
                'failed_requests': len(errors),
                'response_times': {
                    'min': min(response_times),
                    'max': max(response_times),
                    'avg': statistics.mean(response_times),
                    'median': statistics.median(response_times),
                    'stdev': statistics.stdev(response_times) if len(response_times) > 1 else 0
                },
                'data_size': {
                    'min': min(data_sizes) if data_sizes else 0,
                    'max': max(data_sizes) if data_sizes else 0,
                    'avg': statistics.mean(data_sizes) if data_sizes else 0
                },
                'errors': errors
            }
            
            self.results.append(stats)
            return stats
        
        return None
    
    def print_summary(self, stats: Dict):
        """Imprime resumo das estatísticas"""
        print(f"\n📊 RESUMO:")
        print(f"  Requisições bem-sucedidas: {stats['successful_requests']}/{stats['iterations']}")
        print(f"  Requisições falhadas: {stats['failed_requests']}")
        print(f"\n⏱️  TEMPO DE RESPOSTA:")
        print(f"  Mínimo: {stats['response_times']['min']:.2f}ms")
        print(f"  Máximo: {stats['response_times']['max']:.2f}ms")
        print(f"  Média: {stats['response_times']['avg']:.2f}ms")
        print(f"  Mediana: {stats['response_times']['median']:.2f}ms")
        print(f"  Desvio Padrão: {stats['response_times']['stdev']:.2f}ms")
        print(f"\n📦 TAMANHO DOS DADOS:")
        print(f"  Mínimo: {stats['data_size']['min']:,} bytes")
        print(f"  Máximo: {stats['data_size']['max']:,} bytes")
        print(f"  Média: {stats['data_size']['avg']:,.0f} bytes")
        
        if stats['errors']:
            print(f"\n❌ ERROS ({len(stats['errors'])}):")
            for error in set(stats['errors']):
                count = stats['errors'].count(error)
                print(f"  - {error} ({count}x)")
    
    def generate_report(self):
        """Gera relatório completo de performance"""
        print(f"\n\n{'#'*80}")
        print(f"# RELATÓRIO COMPLETO DE PERFORMANCE DA API")
        print(f"# Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"# Base URL: {self.base_url}")
        print(f"{'#'*80}\n")
        
        for i, result in enumerate(self.results, 1):
            print(f"\n{'='*80}")
            print(f"TESTE {i}: {result['endpoint']}")
            if result['params']:
                print(f"Parâmetros: {result['params']}")
            print(f"{'='*80}")
            self.print_summary(result)
        
        # Comparação geral
        print(f"\n\n{'='*80}")
        print(f"COMPARAÇÃO GERAL DE ENDPOINTS")
        print(f"{'='*80}\n")
        
        print(f"{'Endpoint':<40} {'Média (ms)':<15} {'Mediana (ms)':<15} {'Taxa Sucesso'}")
        print(f"{'-'*80}")
        
        for result in self.results:
            endpoint_display = result['endpoint']
            if result['params']:
                endpoint_display += f" ({', '.join(f'{k}={v}' for k, v in result['params'].items())})"
            
            avg_time = result['response_times']['avg']
            median_time = result['response_times']['median']
            success_rate = (result['successful_requests'] / result['iterations']) * 100
            
            print(f"{endpoint_display:<40} {avg_time:<15.2f} {median_time:<15.2f} {success_rate:.1f}%")


def main():
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              ANÁLISE DE PERFORMANCE - API T CrB MONITORING                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    tester = APIPerformanceTester(API_BASE_URL)
    
    # Teste 1: Endpoint raiz (informações da API)
    print("\n🔍 TESTE 1: Endpoint Raiz (GET /)")
    stats1 = tester.test_endpoint("/", iterations=20)
    if stats1:
        tester.print_summary(stats1)
    
    # Teste 2: /latest (última observação)
    print("\n🔍 TESTE 2: Última Observação (GET /latest)")
    stats2 = tester.test_endpoint("/latest", iterations=20)
    if stats2:
        tester.print_summary(stats2)
    
    # Teste 3: /stats (estatísticas)
    print("\n🔍 TESTE 3: Estatísticas (GET /stats)")
    stats3 = tester.test_endpoint("/stats", iterations=20)
    if stats3:
        tester.print_summary(stats3)
    
    # Teste 4: /observations com paginação pequena (10 registros)
    print("\n🔍 TESTE 4: Observações - Página Pequena (limit=10)")
    stats4 = tester.test_endpoint("/observations", params={'page': 1, 'limit': 10}, iterations=15)
    if stats4:
        tester.print_summary(stats4)
    
    # Teste 5: /observations com paginação média (50 registros - padrão)
    print("\n🔍 TESTE 5: Observações - Página Média (limit=50)")
    stats5 = tester.test_endpoint("/observations", params={'page': 1, 'limit': 50}, iterations=15)
    if stats5:
        tester.print_summary(stats5)
    
    # Teste 6: /observations com paginação grande (500 registros)
    print("\n🔍 TESTE 6: Observações - Página Grande (limit=500)")
    stats6 = tester.test_endpoint("/observations", params={'page': 1, 'limit': 500}, iterations=10)
    if stats6:
        tester.print_summary(stats6)
    
    # Teste 7: /observations com paginação máxima (1000 registros)
    print("\n🔍 TESTE 7: Observações - Página Máxima (limit=1000)")
    stats7 = tester.test_endpoint("/observations", params={'page': 1, 'limit': 1000}, iterations=10)
    if stats7:
        tester.print_summary(stats7)
    
    # Teste 8: Páginas diferentes (teste de cache)
    print("\n🔍 TESTE 8: Diferentes Páginas (teste de cache)")
    for page in [1, 10, 100, 500]:
        print(f"\n  Testando página {page}...")
        stats = tester.test_endpoint("/observations", params={'page': page, 'limit': 50}, iterations=5)
        if stats:
            print(f"    Média: {stats['response_times']['avg']:.2f}ms")
    
    # Gera relatório final
    tester.generate_report()
    
    print(f"\n\n{'='*80}")
    print(f"✅ ANÁLISE CONCLUÍDA!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()