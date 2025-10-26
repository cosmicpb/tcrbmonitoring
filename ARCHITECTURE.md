# Arquitetura do Sistema T CrB Monitoring

## Visão Geral

O sistema foi refatorado para usar **dois Cloudflare Workers separados**, seguindo o princípio de **separação de responsabilidades**:

1. **Scraper Worker** - Coleta dados do AAVSO
2. **API Worker** - Serve dados via REST API

Ambos compartilham o mesmo banco de dados **Cloudflare D1**.

---

## 1. Scraper Worker

### Responsabilidade
Coletar automaticamente dados de observações da estrela T CrB do portal AAVSO.

### Características
- **Nome**: `tcrb-scraper`
- **Arquivo**: `scraper-worker.py`
- **Config**: `wrangler-scraper.toml`
- **Trigger**: Cron job (executa a cada hora: `0 * * * *`)
- **URL**: https://tcrb-scraper.pbaldacimjr.workers.dev

### Funcionamento
1. Executa automaticamente a cada hora via cron trigger
2. Faz scraping da página do AAVSO
3. Extrai dados da última observação
4. Salva no banco D1 (evita duplicatas)
5. Registra logs com prefixo `[SCRAPER]`

### Dados Coletados
- Star (estrela)
- JD (Julian Date)
- Calendar Date (formato brasileiro: dd/MM/YYYY HH:mm)
- Magnitude
- Error (erro da medição)
- Filter (banda/filtro usado)
- Observer (código do observador)
- Scraped At (timestamp da coleta)

---

## 2. API Worker

### Responsabilidade
Fornecer acesso aos dados via endpoints REST HTTP.

### Características
- **Nome**: `tcrb-api`
- **Arquivo**: `api-worker.py`
- **Config**: `wrangler-api.toml`
- **Trigger**: HTTP requests
- **URL**: https://tcrb-api.pbaldacimjr.workers.dev

### Endpoints Disponíveis

#### `GET /`
Informações gerais da API
```json
{
  "status": "online",
  "name": "T CrB Monitoring API",
  "version": "2.0",
  "total_observations": 1,
  "endpoints": {...}
}
```

#### `GET /observations?limit=X`
Últimas X observações (padrão: 10, máximo: 100)
```json
{
  "status": "success",
  "total_observations": 1,
  "returned": 1,
  "limit": 5,
  "observations": [...]
}
```

#### `GET /latest`
Última observação coletada
```json
{
  "status": "success",
  "observation": {
    "id": 1,
    "star": "T CrB",
    "magnitude": "11.0339",
    ...
  }
}
```

#### `GET /stats`
Estatísticas gerais
```json
{
  "status": "success",
  "statistics": {
    "total_observations": 1,
    "latest_observation": {...},
    "magnitude_stats": {
      "min": 11.0339,
      "max": 11.0339,
      "average": 11.0339
    }
  }
}
```

### Logs
Todos os logs são prefixados com `[API]` para fácil identificação.

---

## 3. Banco de Dados D1

### Características
- **Nome**: `tcrb-observations`
- **Tipo**: SQLite (Cloudflare D1)
- **Compartilhado**: Ambos os workers acessam o mesmo banco

### Schema
```sql
CREATE TABLE observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    star TEXT NOT NULL,
    jd TEXT NOT NULL,
    calendar_date TEXT NOT NULL,
    magnitude TEXT NOT NULL,
    error TEXT,
    filter TEXT,
    observer TEXT,
    scraped_at TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(jd, magnitude, observer)
);
```

### Índices
```sql
CREATE INDEX idx_created_at ON observations(created_at DESC);
CREATE INDEX idx_calendar_date ON observations(calendar_date DESC);
CREATE INDEX idx_magnitude ON observations(magnitude);
```

---

## 4. Deploy

### Scraper Worker
```bash
npx wrangler deploy --config wrangler-scraper.toml
```

### API Worker
```bash
npx wrangler deploy --config wrangler-api.toml
```

### Monitorar Logs

**Scraper:**
```bash
npx wrangler tail tcrb-scraper --format pretty
```

**API:**
```bash
npx wrangler tail tcrb-api --format pretty
```

---

## 5. Vantagens da Arquitetura

### Separação de Responsabilidades
- Cada worker tem uma função específica e bem definida
- Facilita manutenção e debugging
- Permite escalar independentemente

### Isolamento de Falhas
- Se a API falhar, o scraper continua coletando dados
- Se o scraper falhar, a API continua servindo dados existentes

### Logs Organizados
- Logs separados por worker
- Prefixos `[SCRAPER]` e `[API]` facilitam identificação
- Melhor rastreabilidade de problemas

### Performance
- API responde rapidamente (apenas leitura)
- Scraper não afeta performance da API
- Cron trigger garante coleta regular sem overhead

### Segurança
- API é read-only (não pode modificar dados)
- Scraper é o único que escreve no banco
- Reduz superfície de ataque

---

## 6. Fluxo de Dados

```
┌─────────────────┐
│   AAVSO Portal  │
└────────┬────────┘
         │
         │ HTTP Request (a cada hora)
         ▼
┌─────────────────┐
│ Scraper Worker  │
│  (Cron Trigger) │
└────────┬────────┘
         │
         │ INSERT/UPDATE
         ▼
┌─────────────────┐
│  D1 Database    │
│  (SQLite)       │
└────────┬────────┘
         │
         │ SELECT
         ▼
┌─────────────────┐
│   API Worker    │
│  (HTTP Trigger) │
└────────┬────────┘
         │
         │ JSON Response
         ▼
┌─────────────────┐
│     Clients     │
│ (Web, Apps, etc)│
└─────────────────┘
```

---

## 7. Monitoramento

### Verificar Status da API
```bash
curl https://tcrb-api.pbaldacimjr.workers.dev/
```

### Verificar Última Observação
```bash
curl https://tcrb-api.pbaldacimjr.workers.dev/latest
```

### Verificar Estatísticas
```bash
curl https://tcrb-api.pbaldacimjr.workers.dev/stats
```

### Logs em Tempo Real
```bash
# Scraper
npx wrangler tail tcrb-scraper --format pretty

# API
npx wrangler tail tcrb-api --format pretty
```

---

## 8. Próximos Passos

### Melhorias Futuras
- [ ] Adicionar autenticação na API (API keys)
- [ ] Implementar rate limiting
- [ ] Adicionar cache (KV ou Cache API)
- [ ] Criar dashboard web para visualização
- [ ] Adicionar alertas (email/webhook) para magnitudes anormais
- [ ] Implementar paginação nos endpoints
- [ ] Adicionar filtros por data/magnitude
- [ ] Criar endpoint para exportar dados (CSV/JSON)

### Dados Históricos
- Script `historical_scraper.py` disponível para coletar dados históricos
- Script `import_to_d1.py` para importar dados locais para D1
- Ver `HISTORICAL_DATA.md` para instruções detalhadas

---

## 9. Troubleshooting

### API retorna vazio
- Verificar se o banco D1 está configurado corretamente
- Verificar logs: `npx wrangler tail tcrb-api`
- Testar query diretamente no D1: `npx wrangler d1 execute tcrb-observations --command "SELECT COUNT(*) FROM observations"`

### Scraper não coleta dados
- Verificar logs: `npx wrangler tail tcrb-scraper`
- Verificar se o cron trigger está ativo
- Testar manualmente: acessar URL do scraper worker

### Dados duplicados
- O sistema usa `UNIQUE(jd, magnitude, observer)` para evitar duplicatas
- Se houver duplicatas, verificar se o constraint está ativo

---

## 10. Contato e Suporte

Para dúvidas ou problemas:
- Verificar logs dos workers
- Consultar documentação do Cloudflare Workers
- Revisar código fonte nos arquivos `.py`