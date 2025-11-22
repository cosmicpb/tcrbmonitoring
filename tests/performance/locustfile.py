"""
Locust Load Testing - API T CrB Monitoring
Testes de carga e performance para análise detalhada da API
"""

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import random
import time
import json

class TCrBAPIUser(HttpUser):
    """
    Simula um usuário da API T CrB
    Testa diferentes endpoints com pesos diferentes
    """
    
    # Tempo de espera entre requisições (simula comportamento real)
    wait_time = between(1, 3)
    
    def on_start(self):
        """Executado quando o usuário inicia"""
        print(f"[USER] Novo usuário iniciado")
    
    @task(10)
    def get_root(self):
        """
        Endpoint raiz - informações da API
        Peso: 10 (mais comum)
        """
        with self.client.get("/", catch_response=True, name="GET /") as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('status') == 'online':
                        response.success()
                    else:
                        response.failure(f"Status não é 'online': {data.get('status')}")
                except json.JSONDecodeError:
                    response.failure("Resposta não é JSON válido")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(8)
    def get_latest(self):
        """
        Última observação
        Peso: 8 (muito usado)
        """
        with self.client.get("/latest", catch_response=True, name="GET /latest") as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('status') == 'success':
                        response.success()
                    else:
                        response.failure(f"Status não é 'success': {data.get('status')}")
                except json.JSONDecodeError:
                    response.failure("Resposta não é JSON válido")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(6)
    def get_stats(self):
        """
        Estatísticas
        Peso: 6 (usado frequentemente)
        """
        with self.client.get("/stats", catch_response=True, name="GET /stats") as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('status') == 'success':
                        response.success()
                    else:
                        response.failure(f"Status não é 'success': {data.get('status')}")
                except json.JSONDecodeError:
                    response.failure("Resposta não é JSON válido")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(15)
    def get_observations_small(self):
        """
        Observações - página pequena (10 registros)
        Peso: 15 (muito usado - paginação pequena)
        """
        page = random.randint(1, 100)
        with self.client.get(
            "/observations",
            params={"page": page, "limit": 10},
            catch_response=True,
            name="GET /observations (limit=10)"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('status') == 'success':
                        response.success()
                    else:
                        response.failure(f"Status não é 'success': {data.get('status')}")
                except json.JSONDecodeError:
                    response.failure("Resposta não é JSON válido")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(10)
    def get_observations_medium(self):
        """
        Observações - página média (50 registros - padrão)
        Peso: 10 (uso comum)
        """
        page = random.randint(1, 50)
        with self.client.get(
            "/observations",
            params={"page": page, "limit": 50},
            catch_response=True,
            name="GET /observations (limit=50)"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('status') == 'success':
                        response.success()
                    else:
                        response.failure(f"Status não é 'success': {data.get('status')}")
                except json.JSONDecodeError:
                    response.failure("Resposta não é JSON válido")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(5)
    def get_observations_large(self):
        """
        Observações - página grande (500 registros)
        Peso: 5 (uso menos frequente)
        """
        page = random.randint(1, 10)
        with self.client.get(
            "/observations",
            params={"page": page, "limit": 500},
            catch_response=True,
            name="GET /observations (limit=500)"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('status') == 'success':
                        response.success()
                    else:
                        response.failure(f"Status não é 'success': {data.get('status')}")
                except json.JSONDecodeError:
                    response.failure("Resposta não é JSON válido")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(2)
    def get_observations_max(self):
        """
        Observações - página máxima (1000 registros)
        Peso: 2 (uso raro - teste de stress)
        """
        page = random.randint(1, 5)
        with self.client.get(
            "/observations",
            params={"page": page, "limit": 1000},
            catch_response=True,
            name="GET /observations (limit=1000)"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('status') == 'success':
                        response.success()
                    else:
                        response.failure(f"Status não é 'success': {data.get('status')}")
                except json.JSONDecodeError:
                    response.failure("Resposta não é JSON válido")
            else:
                response.failure(f"Status code: {response.status_code}")


# Event listeners para estatísticas customizadas
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Executado quando o teste inicia"""
    print("\n" + "="*80)
    print("🚀 INICIANDO TESTE DE CARGA - API T CrB Monitoring")
    print("="*80)
    print(f"Host: {environment.host}")
    print(f"Usuários: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("="*80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Executado quando o teste termina"""
    print("\n" + "="*80)
    print("✅ TESTE DE CARGA CONCLUÍDO")
    print("="*80)
    
    stats = environment.stats
    
    print("\n📊 RESUMO GERAL:")
    print(f"  Total de requisições: {stats.total.num_requests}")
    print(f"  Requisições falhadas: {stats.total.num_failures}")
    print(f"  Taxa de sucesso: {((stats.total.num_requests - stats.total.num_failures) / stats.total.num_requests * 100):.2f}%")
    print(f"  Tempo médio de resposta: {stats.total.avg_response_time:.2f}ms")
    print(f"  Tempo mediano de resposta: {stats.total.median_response_time:.2f}ms")
    print(f"  Requisições por segundo: {stats.total.total_rps:.2f}")
    
    print("\n📈 PERCENTIS DE TEMPO DE RESPOSTA:")
    print(f"  50%: {stats.total.get_response_time_percentile(0.50):.2f}ms")
    print(f"  75%: {stats.total.get_response_time_percentile(0.75):.2f}ms")
    print(f"  90%: {stats.total.get_response_time_percentile(0.90):.2f}ms")
    print(f"  95%: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"  99%: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    
    print("\n🔝 TOP 5 ENDPOINTS MAIS LENTOS:")
    sorted_stats = sorted(
        [s for s in stats.entries.values() if s.num_requests > 0],
        key=lambda x: x.avg_response_time,
        reverse=True
    )[:5]
    
    for i, stat in enumerate(sorted_stats, 1):
        print(f"  {i}. {stat.name}")
        print(f"     Tempo médio: {stat.avg_response_time:.2f}ms")
        print(f"     Requisições: {stat.num_requests}")
        print(f"     Falhas: {stat.num_failures}")
    
    print("\n" + "="*80 + "\n")


# Configuração para diferentes cenários de teste
class LightLoadUser(TCrBAPIUser):
    """Carga leve - simula uso normal"""
    wait_time = between(2, 5)


class HeavyLoadUser(TCrBAPIUser):
    """Carga pesada - simula picos de uso"""
    wait_time = between(0.5, 2)


class StressTestUser(TCrBAPIUser):
    """Teste de stress - carga máxima"""
    wait_time = between(0.1, 0.5)