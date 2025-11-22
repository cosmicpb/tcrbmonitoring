# 🔒 Segurança e Rate Limiting da API T CrB

## 📋 Visão Geral

A API T CrB implementa múltiplas camadas de segurança para proteger contra abuso, garantir disponibilidade e melhorar performance.

---

## 🛡️ Recursos de Segurança Implementados

### 1. **Rate Limiting** ⏱️

Limita o número de requisições por IP para prevenir abuso e garantir disponibilidade.

**Configuração Atual:**
- **Limite**: 100 requisições por minuto por IP
- **Janela**: 60 segundos
- **Status**: ✅ Ativo

**Como funciona:**
- Cada IP tem um contador de requisições
- Contador reseta a cada minuto
- Quando limite é atingido, retorna HTTP 429 (Too Many Requests)
- Headers de resposta incluem informações de rate limit

**Resposta quando limite é excedido:**
```json
{
  "status": "error",
  "message": "Rate limit exceeded",
  "retry_after": 45
}
```

**Headers de Rate Limit em todas as respostas:**
```json
{
  "rate_limit": {
    "remaining": 95,
    "reset": 1699876543
  }
}
```

---

### 2. **CORS (Cross-Origin Resource Sharing)** 🌐

Permite que aplicações web de outros domínios consumam a API.

**Headers configurados:**
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

**Suporte a Preflight:**
- Requisições OPTIONS são tratadas automaticamente
- Retorna 200 OK com headers CORS

---

### 3. **Cache Headers** 💾

Melhora performance e reduz carga no servidor.

**TTL por endpoint:**
- `/observations`: 30 segundos
- `/latest`: 60 segundos (1 minuto)
- `/stats`: 300 segundos (5 minutos)
- `/` (info): 60 segundos

**Headers configurados:**
```
Cache-Control: public, max-age=300
```

**Benefícios:**
- Reduz latência para usuários
- Diminui carga no D1
- Economiza recursos do Worker

---

### 4. **Security Headers** 🔐

Protege contra ataques comuns.

**Headers implementados:**
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
```

**Proteções:**
- **nosniff**: Previne MIME type sniffing
- **DENY**: Previne clickjacking (não pode ser embutido em iframe)
- **XSS Protection**: Ativa proteção contra XSS no browser

---

### 5. **Validação de Parâmetros** ✅

Valida e sanitiza todos os parâmetros de entrada.

**Validações implementadas:**

**Paginação:**
- `page`: Deve ser >= 1 (padrão: 1)
- `limit`: Deve estar entre 1 e 1000 (padrão: 50)
- Valores inválidos retornam HTTP 400

**Exemplo de erro:**
```json
{
  "status": "error",
  "message": "Limit must be between 1 and 1000"
}
```

---

### 6. **Logging e Monitoramento** 📊

Registra todas as requisições para auditoria e debugging.

**Informações logadas:**
- IP do cliente
- Método HTTP
- Endpoint acessado
- Parâmetros da query
- Status do rate limit
- Erros e exceções

**Exemplo de log:**
```
[API] 192.168.1.1 -> GET /observations | Params: {'page': '1', 'limit': '50'}
[API] ⚠️  192.168.1.1 has 5 requests remaining
```

---

## 🚀 Configuração Avançada

### Ativar KV para Rate Limiting (Recomendado)

O rate limiting atual funciona em memória. Para produção com múltiplas instâncias, use KV:

**1. Criar KV Namespace:**
```bash
npx wrangler kv:namespace create "RATE_LIMIT_KV"
```

**2. Anotar o ID retornado:**
```
{ binding = "RATE_LIMIT_KV", id = "abc123..." }
```

**3. Atualizar wrangler-api.toml:**
```toml
[[kv_namespaces]]
binding = "RATE_LIMIT_KV"
id = "abc123..."  # ID do passo 2
```

**4. Deploy:**
```bash
npx wrangler deploy --config wrangler-api.toml
```

**Benefícios do KV:**
- Rate limiting compartilhado entre todas as instâncias
- Persistência entre deploys
- Melhor precisão em ambientes distribuídos

---

## ⚙️ Ajustando Configurações

### Modificar Limites de Rate

Edite [`api-worker.py`](api-worker.py:10):

```python
# Configurações de Rate Limiting
RATE_LIMIT_WINDOW = 60  # Janela em segundos
RATE_LIMIT_MAX_REQUESTS = 100  # Máximo de requisições
RATE_LIMIT_ENABLED = True  # Ativar/desativar
```

**Exemplos de configuração:**

**Mais restritivo (APIs públicas):**
```python
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 30  # 30 req/min
```

**Mais permissivo (uso interno):**
```python
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 300  # 300 req/min
```

**Desativar (desenvolvimento):**
```python
RATE_LIMIT_ENABLED = False
```

---

### Modificar TTL de Cache

Edite [`api-worker.py`](api-worker.py:13):

```python
# Configurações de Cache
CACHE_TTL_STATS = 300  # 5 minutos
CACHE_TTL_LATEST = 60  # 1 minuto
CACHE_TTL_OBSERVATIONS = 30  # 30 segundos
```

**Recomendações:**
- Dados que mudam raramente: 300-600 segundos
- Dados que mudam frequentemente: 30-60 segundos
- Dados em tempo real: 0 (sem cache)

---

### Modificar CORS

Para restringir origens permitidas, edite [`api-worker.py`](api-worker.py:35):

```python
# Permitir apenas domínios específicos
allowed_origins = [
    "https://seu-site.com",
    "https://app.seu-site.com"
]

origin = request.headers.get('Origin')
if origin in allowed_origins:
    headers.set("Access-Control-Allow-Origin", origin)
else:
    headers.set("Access-Control-Allow-Origin", "https://seu-site.com")
```

---

## 📊 Monitoramento

### Verificar Rate Limit

Todas as respostas incluem informações de rate limit:

```bash
curl -i https://tcrb-api.pbaldacimjr.workers.dev/
```

Procure por:
```json
{
  "rate_limit": {
    "remaining": 95,
    "reset": 1699876543
  }
}
```

---

### Logs no Cloudflare

**Ver logs em tempo real:**
```bash
npx wrangler tail --config wrangler-api.toml
```

**Filtrar por IP:**
```bash
npx wrangler tail --config wrangler-api.toml | grep "192.168.1.1"
```

**Filtrar rate limit warnings:**
```bash
npx wrangler tail --config wrangler-api.toml | grep "⚠️"
```

---

### Analytics no Dashboard

1. Acesse: https://dash.cloudflare.com
2. Selecione sua conta
3. Workers & Pages → tcrb-api
4. Aba "Metrics"

**Métricas disponíveis:**
- Total de requisições
- Requisições por segundo
- Erros (4xx, 5xx)
- Latência (p50, p95, p99)
- CPU time
- Bandwidth

---

## 🔧 Troubleshooting

### Problema: Rate limit muito restritivo

**Sintoma:** Usuários legítimos sendo bloqueados

**Solução:**
1. Aumentar `RATE_LIMIT_MAX_REQUESTS`
2. Aumentar `RATE_LIMIT_WINDOW`
3. Implementar whitelist de IPs confiáveis

---

### Problema: Cache desatualizado

**Sintoma:** Dados antigos sendo retornados

**Solução:**
1. Reduzir TTL de cache
2. Implementar cache invalidation
3. Adicionar parâmetro `?nocache=1` para bypass

---

### Problema: CORS bloqueando requisições

**Sintoma:** Erro "CORS policy" no browser

**Solução:**
1. Verificar se OPTIONS está funcionando
2. Verificar headers CORS na resposta
3. Adicionar origem específica se necessário

---

## 📈 Melhores Práticas

### 1. **Monitoramento Contínuo**
- Configure alertas para rate limit excessivo
- Monitore latência e erros
- Revise logs regularmente

### 2. **Ajuste Gradual**
- Comece com limites conservadores
- Ajuste baseado em métricas reais
- Teste mudanças em staging primeiro

### 3. **Documentação**
- Documente limites na documentação da API
- Informe usuários sobre rate limits
- Forneça exemplos de tratamento de erros

### 4. **Backup e Redundância**
- Use KV para rate limiting distribuído
- Configure múltiplas regiões se necessário
- Tenha plano de fallback para falhas

---

## 🎯 Próximos Passos

### Melhorias Futuras

1. **Autenticação por API Key**
   - Limites diferentes por tier (free/pro)
   - Tracking de uso por usuário
   - Billing baseado em uso

2. **Rate Limiting Avançado**
   - Limites por endpoint
   - Burst allowance
   - Sliding window

3. **WAF (Web Application Firewall)**
   - Proteção contra SQL injection
   - Proteção contra XSS
   - Bot detection

4. **Caching Avançado**
   - Cache warming
   - Stale-while-revalidate
   - Cache tags para invalidation

---

## 📞 Suporte

Para questões sobre segurança:
- Revise logs: `npx wrangler tail`
- Consulte métricas no dashboard
- Verifique documentação do Cloudflare Workers

---

**Última atualização:** 2025-11-13  
**Versão da API:** 2.1  
**Status:** ✅ Produção