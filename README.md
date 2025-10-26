# T CrB Monitoring System

Sistema de monitoramento automático da estrela T Coronae Borealis (T CrB) usando **Cloudflare Workers** e **D1 Database**.

## 🌟 Sobre T CrB

T Coronae Borealis é uma **nova recorrente** - um sistema binário onde uma anã branca acumula material de uma gigante vermelha. Periodicamente (aproximadamente a cada 80 anos), esse material acumulado causa uma explosão termonuclear, aumentando o brilho da estrela em cerca de **10 magnitudes**.

A última erupção foi em **1946**, e astrônomos preveem que uma nova erupção pode ocorrer a qualquer momento entre **2024-2026**. Este sistema monitora continuamente a estrela para detectar qualquer mudança significativa.

---

## 🏗️ Arquitetura

O sistema utiliza **dois Cloudflare Workers separados** seguindo o princípio de separação de responsabilidades:

### 1. 🤖 Scraper Worker
- **Função**: Coleta automática de dados do AAVSO
- **Trigger**: Cron job (executa a cada hora: `0 * * * *`)
- **Arquivo**: [`scraper-worker.py`](scraper-worker.py)
- **Config**: [`wrangler-scraper.toml`](wrangler-scraper.toml)
- **URL**: https://tcrb-scraper.pbaldacimjr.workers.dev

### 2. 🌐 API Worker
- **Função**: Serve dados via REST API
- **Trigger**: HTTP requests
- **Arquivo**: [`api-worker.py`](api-worker.py)
- **Config**: [`wrangler-api.toml`](wrangler-api.toml)
- **URL**: https://tcrb-api.pbaldacimjr.workers.dev

### 💾 Banco de Dados
- **Cloudflare D1** (SQLite serverless)
- Compartilhado entre ambos os workers
- Schema: [`schema_d1.sql`](schema_d1.sql)

📖 **Documentação completa da arquitetura**: [`ARCHITECTURE.md`](ARCHITECTURE.md)

---

## ✨ Funcionalidades

- ✅ Coleta automática de dados do AAVSO a cada hora
- ✅ API REST para consultar observações
- ✅ Armazenamento em Cloudflare D1 (SQLite)
- ✅ Conversão automática de datas para formato brasileiro (dd/MM/YYYY HH:mm)
- ✅ Logs detalhados com prefixos `[SCRAPER]` e `[API]`
- ✅ Prevenção de duplicatas (constraint UNIQUE)
- ✅ Estatísticas de magnitude (min, max, média)
- ✅ Script para coleta de dados históricos
- ✅ Zero custo (Free tier do Cloudflare)

---

## 🚀 API Endpoints

### `GET /`
Informações gerais da API

**Exemplo:**
```bash
curl https://tcrb-api.pbaldacimjr.workers.dev/
```

**Resposta:**
```json
{
  "status": "online",
  "name": "T CrB Monitoring API",
  "version": "2.0",
  "total_observations": 1,
  "endpoints": {
    "GET /": "Informações da API",
    "GET /observations?limit=X": "Últimas X observações",
    "GET /latest": "Última observação coletada",
    "GET /stats": "Estatísticas gerais"
  }
}
```

### `GET /observations?limit=X`
Últimas X observações (padrão: 10, máximo: 100)

**Exemplo:**
```bash
curl "https://tcrb-api.pbaldacimjr.workers.dev/observations?limit=5"
```

**Resposta:**
```json
{
  "status": "success",
  "total_observations": 1,
  "returned": 1,
  "limit": 5,
  "observations": [
    {
      "id": 1,
      "star": "T CrB",
      "jd": "2460974.60777406",
      "calendar_date": "26/10/2025 02:35",
      "magnitude": "11.0339",
      "error": "0.0008",
      "filter": "B",
      "observer": "WGR",
      "scraped_at": "26/10/2025 14:26",
      "created_at": "2025-10-26 14:26:41"
    }
  ]
}
```

### `GET /latest`
Última observação coletada

**Exemplo:**
```bash
curl https://tcrb-api.pbaldacimjr.workers.dev/latest
```

### `GET /stats`
Estatísticas gerais (total, magnitude min/max/média)

**Exemplo:**
```bash
curl https://tcrb-api.pbaldacimjr.workers.dev/stats
```

**Resposta:**
```json
{
  "status": "success",
  "statistics": {
    "total_observations": 1,
    "latest_observation": {
      "date": "26/10/2025 02:35",
      "magnitude": "11.0339"
    },
    "magnitude_stats": {
      "min": 11.0339,
      "max": 11.0339,
      "average": 11.0339
    }
  }
}
```

---

## 📊 Dados Coletados

Para cada observação, são extraídos:
- **Star**: Nome da estrela (T CrB)
- **JD**: Data Juliana (Julian Date)
- **Calendar Date**: Data no formato brasileiro (dd/MM/YYYY HH:mm)
- **Magnitude**: Magnitude observada
- **Error**: Margem de erro da medição
- **Filter**: Filtro/banda utilizado (B, V, R, etc.)
- **Observer**: Código do observador AAVSO
- **Scraped At**: Timestamp da coleta (formato brasileiro)
- **Created At**: Timestamp de inserção no banco

---

## 🚀 Deploy

### Pré-requisitos

- Node.js 20+
- Conta Cloudflare (gratuita)
- Wrangler CLI

### 1. Instalar Wrangler

```bash
npm install -g wrangler
```

### 2. Login no Cloudflare

```bash
wrangler login
```

### 3. Criar Banco D1

```bash
wrangler d1 create tcrb-observations
```

Copie o `database_id` retornado e atualize nos arquivos `wrangler-scraper.toml` e `wrangler-api.toml`.

### 4. Criar Schema do Banco

```bash
wrangler d1 execute tcrb-observations --file=schema_d1.sql
```

### 5. Deploy dos Workers

**Scraper Worker:**
```bash
npx wrangler deploy --config wrangler-scraper.toml
```

**API Worker:**
```bash
npx wrangler deploy --config wrangler-api.toml
```

---

## 📈 Monitoramento

### Ver Logs em Tempo Real

**Scraper:**
```bash
npx wrangler tail tcrb-scraper --format pretty
```

**API:**
```bash
npx wrangler tail tcrb-api --format pretty
```

### Consultar Banco D1

```bash
# Total de observações
npx wrangler d1 execute tcrb-observations --command "SELECT COUNT(*) FROM observations"

# Últimas 10 observações
npx wrangler d1 execute tcrb-observations --command "SELECT * FROM observations ORDER BY created_at DESC LIMIT 10"

# Estatísticas de magnitude
npx wrangler d1 execute tcrb-observations --command "SELECT MIN(CAST(magnitude AS REAL)) as min, MAX(CAST(magnitude AS REAL)) as max, AVG(CAST(magnitude AS REAL)) as avg FROM observations WHERE magnitude != ''"
```

---

## 📚 Dados Históricos

O projeto inclui scripts para coletar e importar dados históricos do AAVSO:

### Coletar Dados Históricos

```bash
python historical_scraper.py
```

Este script coleta **~720,000 observações** de **~3,600 páginas** do AAVSO e salva em um banco SQLite local (`data/tcrb_observations.db`).

### Importar para D1

```bash
python import_to_d1.py
```

Este script importa os dados do SQLite local para o banco D1 na Cloudflare.

📖 **Documentação completa**: [`HISTORICAL_DATA.md`](HISTORICAL_DATA.md)

---

## 🗄️ Schema do Banco

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

CREATE INDEX idx_created_at ON observations(created_at DESC);
CREATE INDEX idx_calendar_date ON observations(calendar_date DESC);
CREATE INDEX idx_magnitude ON observations(magnitude);
```

---

## 🛠️ Tecnologias

### Backend (Workers)
- **Python 3.12** (via Pyodide no Cloudflare Workers)
- **BeautifulSoup4** - Parsing HTML
- **Cloudflare Workers** - Serverless compute
- **Cloudflare D1** - SQLite serverless

### Scripts Locais
- **Python 3.8+**
- **Requests** - HTTP requests
- **SQLite3** - Banco local para dados históricos
- **python-dotenv** - Variáveis de ambiente

---

## 📁 Estrutura do Projeto

```
tcrbmonitoring/
├── scraper-worker.py          # Worker de scraping (cron)
├── api-worker.py              # Worker da API (HTTP)
├── wrangler-scraper.toml      # Config do scraper
├── wrangler-api.toml          # Config da API
├── schema_d1.sql              # Schema do D1
├── historical_scraper.py      # Script para dados históricos
├── import_to_d1.py            # Script para importar para D1
├── ARCHITECTURE.md            # Documentação da arquitetura
├── HISTORICAL_DATA.md         # Documentação de dados históricos
├── CLOUDFLARE_DEPLOY.md       # Guia de deploy
└── data/                      # Dados locais (SQLite)
```

---

## 🔄 Fluxo de Dados

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

## 💰 Custos

O sistema roda **100% gratuito** no free tier do Cloudflare:

- **Workers**: 100,000 requests/dia grátis
- **D1**: 5 GB storage + 5 milhões reads/dia grátis
- **Cron Triggers**: Incluído no free tier

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Abra uma issue ou pull request.

---

## 📝 Licença

MIT

---

## 🌐 Fonte dos Dados

Dados coletados do portal oficial da AAVSO:
https://apps.aavso.org/webobs/results/?star=t+crb

---

## 📧 Contato

Para dúvidas ou sugestões, abra uma issue no repositório.