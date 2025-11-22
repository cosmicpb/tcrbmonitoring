# 📊 Análise de Performance da API T CrB

## 🎯 Objetivo

Mapear a performance da API em diferentes cenários de carga para identificar:
- Tempos de resposta por endpoint
- Capacidade de throughput (requisições/segundo)
- Comportamento sob carga
- Gargalos e pontos de otimização

## 🛠️ Ferramentas

### Locust (Recomendado)
Framework profissional de teste de carga em Python com interface web interativa.

**Vantagens:**
- Interface web em tempo real
- Distribuição de carga
- Métricas detalhadas
- Gráficos e relatórios
- Simulação realista de usuários

## 📋 Pré-requisitos

```bash
# Ativar ambiente virtual
. venv/bin/activate

# Instalar Locust (já instalado)
pip install locust
```

## 🚀 Executando Testes

### 1. Teste Básico (Interface Web)

```bash
# Ativar venv
. venv/bin/activate

# Iniciar Locust com interface web
locust -f locustfile.py --host=https://tcrb-api.pbaldacimjr.workers.dev

# Acessar: http://localhost:8089
# Configurar:
#   - Number of users: 10-50 (usuários simultâneos)
#   - Spawn rate: 1-5 (usuários/segundo)
#   - Host: já configurado
```

### 2. Teste Headless (Linha de Comando)

```bash
# Teste rápido: 10 usuários por 30 segundos
locust -f locustfile.py \
  --host=https://tcrb-api.pbaldacimjr.workers.dev \
  --users 10 \
  --spawn-rate 2 \
  --run-time 30s \
  --headless

# Teste médio: 50 usuários por 2 minutos
locust -f locustfile.py \
  --host=https://tcrb-api.pbaldacimjr.workers.dev \
  --users 50 \
  --spawn-rate 5 \
  --run-time 2m \
  --headless

# Teste de stress: 100 usuários por 5 minutos
locust -f locustfile.py \
  --host=https://tcrb-api.pbaldacimjr.workers.dev \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless
```

### 3. Teste com Relatório HTML

```bash
locust -f locustfile.py \
  --host=https://tcrb-api.pbaldacimjr.workers.dev \
  --users 50 \
  --spawn-rate 5 \
  --run-time 2m \
  --headless \
  --html reports/performance_report.html \
  --csv reports/performance_data
```

## 📊 Cenários de Teste

### Cenário 1: Carga Leve (Uso Normal)
```bash
locust -f locustfile.py \
  --host=https://tcrb-api.pbaldacimjr.workers.dev \
  --users 10 \
  --spawn-rate 1 \
  --run-time 1m \
  --headless
```
**Objetivo:** Simular uso normal da API (10 usuários simultâneos)

### Cenário 2: Carga Média (Pico de Uso)
```bash
locust -f locustfile.py \
  --host=https://tcrb-api.pbaldacimjr.workers.dev \
  --users 50 \
  --spawn-rate 5 \
  --run-time 3m \
  --headless
```
**Objetivo:** Simular pico de uso (50 usuários simultâneos)

### Cenário 3: Teste de Stress (Carga Máxima)
```bash
locust -f locustfile.py \
  --host=https://tcrb-api.pbaldacimjr.workers.dev \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless
```
**Objetivo:** Identificar limites da API (100 usuários simultâneos)

### Cenário 4: Teste de Endurance (Longa Duração)
```bash
locust -f locustfile.py \
  --host=https://tcrb-api.pbaldacimjr.workers.dev \
  --users 30 \
  --spawn-rate 3 \
  --run-time 10m \
  --headless
```
**Objetivo:** Verificar estabilidade ao longo do tempo

## 📈 Métricas Analisadas

### 1. Tempo de Resposta
- **Média**: Tempo médio de resposta
- **Mediana**: Tempo que 50% das requisições ficam abaixo
- **P95**: 95% das requisições ficam abaixo deste tempo
- **P99**: 99% das requisições ficam abaixo deste tempo
- **Máximo**: Pior tempo de resposta

### 2. Throughput
- **RPS (Requests Per Second)**: Requisições por segundo
- **Total de Requisições**: Número total de requisições
- **Taxa de Sucesso**: Porcentagem de requisições bem-sucedidas

### 3. Erros
- **Taxa de Erro**: Porcentagem de requisições falhadas
- **Tipos de Erro**: HTTP 4xx, 5xx, timeouts, etc.

## 🎯 Endpoints Testados

| Endpoint | Peso | Descrição |
|----------|------|-----------|
| `GET /` | 10 | Informações da API |
| `GET /latest` | 8 | Última observação |
| `GET /stats` | 6 | Estatísticas |
| `GET /observations?limit=10` | 15 | Paginação pequena |
| `GET /observations?limit=50` | 10 | Paginação média (padrão) |
| `GET /observations?limit=500` | 5 | Paginação grande |
| `GET /observations?limit=1000` | 2 | Paginação máxima |

**Peso**: Frequência relativa de cada endpoint (maior = mais requisições)

## 🔍 Análise de Resultados

### Tempos de Resposta Esperados (Cloudflare Workers)

| Endpoint | Esperado | Aceitável | Crítico |
|----------|----------|-----------|---------|
| `GET /` | < 50ms | < 100ms | > 200ms |
| `GET /latest` | < 100ms | < 200ms | > 500ms |
| `GET /stats` | < 150ms | < 300ms | > 600ms |
| `GET /observations (10)` | < 100ms | < 200ms | > 500ms |
| `GET /observations (50)` | < 200ms | < 400ms | > 800ms |
| `GET /observations (500)` | < 500ms | < 1000ms | > 2000ms |
| `GET /observations (1000)` | < 1000ms | < 2000ms | > 4000ms |

### Capacidade Esperada

- **Cloudflare Workers**: ~1000-10000 RPS (dependendo da complexidade)
- **D1 Database**: ~100-1000 queries/segundo
- **Rate Limit**: 100 requisições/minuto por IP

## 🎨 Interface Web do Locust

Ao executar com interface web (`locust -f locustfile.py --host=...`):

1. **Acesse**: http://localhost:8089
2. **Configure**:
   - Number of users: Usuários simultâneos
   - Spawn rate: Usuários adicionados por segundo
3. **Inicie o teste**
4. **Monitore em tempo real**:
   - Gráficos de RPS
   - Tempos de resposta
   - Número de usuários
   - Taxa de erro

## 📁 Estrutura de Arquivos

```
tcrbmonitoring/
├── locustfile.py              # Definição dos testes
├── API_PERFORMANCE_TESTING.md # Este documento
├── test_api_performance.py    # Script alternativo (requests)
└── reports/                   # Relatórios gerados
    ├── performance_report.html
    ├── performance_data_stats.csv
    └── performance_data_failures.csv
```

## 🔧 Configurações Avançadas

### Teste Distribuído (Múltiplas Máquinas)

```bash
# Máquina Master
locust -f locustfile.py --master --host=https://tcrb-api.pbaldacimjr.workers.dev

# Máquinas Workers (em outras máquinas)
locust -f locustfile.py --worker --master-host=<IP_DO_MASTER>
```

### Classes de Usuário Customizadas

O `locustfile.py` inclui 3 classes:
- `TCrBAPIUser`: Comportamento padrão
- `LightLoadUser`: Carga leve (wait_time maior)
- `HeavyLoadUser`: Carga pesada (wait_time menor)
- `StressTestUser`: Teste de stress (wait_time mínimo)

Para usar uma classe específica:
```bash
locust -f locustfile.py --host=... --user-classes StressTestUser
```

## 📊 Exemplo de Análise

### Resultado Esperado (Bom)
```
Total requests: 10000
Failures: 0 (0%)
Average response time: 150ms
Median response time: 120ms
95th percentile: 300ms
99th percentile: 500ms
RPS: 50
```

### Resultado Problemático
```
Total requests: 10000
Failures: 500 (5%)
Average response time: 2000ms
Median response time: 1500ms
95th percentile: 5000ms
99th percentile: 10000ms
RPS: 10
```

## 🎯 Próximos Passos

1. **Executar teste baseline** (10 usuários, 1 minuto)
2. **Analisar resultados**
3. **Identificar gargalos**
4. **Otimizar endpoints lentos**
5. **Re-testar para validar melhorias**

## 📚 Recursos

- [Documentação Locust](https://docs.locust.io/)
- [Cloudflare Workers Performance](https://developers.cloudflare.com/workers/platform/limits/)
- [D1 Database Limits](https://developers.cloudflare.com/d1/platform/limits/)