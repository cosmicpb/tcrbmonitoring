# Análise de Schemas - SQLite vs D1

## 📊 Comparação de Schemas

### SQLite Local (data/tcrb_observations.db)
```sql
CREATE TABLE observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    star TEXT NOT NULL,
    jd TEXT NOT NULL,                    -- ⚠️ Julian Date
    calendar_date TEXT NOT NULL,         -- ⚠️ Data formatada
    magnitude REAL NOT NULL,
    error REAL,
    band TEXT,                           -- ⚠️ Filtro
    observer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(star, jd, magnitude, band, observer)
);
```

### D1 (Cloudflare) - Schema Real
```sql
CREATE TABLE observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    star TEXT NOT NULL,
    jd TEXT NOT NULL,                    -- ✅ Julian Date
    calendar_date TEXT NOT NULL,         -- ✅ Data formatada
    magnitude TEXT NOT NULL,             -- ⚠️ TEXT (não REAL)
    error TEXT,                          -- ⚠️ TEXT (não REAL)
    filter TEXT,                         -- ⚠️ "filter" (não "band")
    observer TEXT,
    scraped_at TEXT,                     -- ✅ Adicional
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### schema_d1.sql (Arquivo desatualizado)
```sql
CREATE TABLE observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    star TEXT NOT NULL,
    date_original TEXT NOT NULL,         -- ❌ ERRADO (deveria ser "jd")
    date_br TEXT NOT NULL,               -- ❌ ERRADO (deveria ser "calendar_date")
    magnitude REAL NOT NULL,
    error REAL,
    band TEXT,                           -- ❌ ERRADO (deveria ser "filter")
    observer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(star, date_original, magnitude, band, observer)
);
```

## 🔴 Problemas Identificados

### 1. Schema D1 Real vs Arquivo
O arquivo [`schema_d1.sql`](schema_d1.sql:1) está **desatualizado** e não reflete o schema real do D1.

**Diferenças:**
- `date_original` → deveria ser `jd`
- `date_br` → deveria ser `calendar_date`
- `band` → deveria ser `filter`
- Falta campo `scraped_at`

### 2. Script de Migração Incorreto
O [`migrate_to_d1.py`](migrate_to_d1.py:31) tenta ler colunas que **não existem** no SQLite:

```python
# Linha 31-42: ERRADO
cursor.execute("""
    SELECT
        star,
        date_original,  # ❌ Não existe no SQLite (é "jd")
        date_br,        # ❌ Não existe no SQLite (é "calendar_date")
        magnitude,
        error,
        CASE
            WHEN band IS NOT NULL AND band != '' THEN band
            ELSE NULL
        END as band,    # ⚠️ No D1 é "filter"
        observer
    FROM observations
""")
```

### 3. Tipos de Dados Diferentes
- **SQLite**: `magnitude REAL`, `error REAL`
- **D1**: `magnitude TEXT`, `error TEXT`

Isso não é problema crítico, mas pode afetar queries numéricas.

## ✅ Correções Necessárias

### 1. Atualizar schema_d1.sql
```sql
CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    star TEXT NOT NULL,
    jd TEXT NOT NULL,
    calendar_date TEXT NOT NULL,
    magnitude TEXT NOT NULL,
    error TEXT,
    filter TEXT,
    observer TEXT,
    scraped_at TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(star, jd, magnitude, filter, observer)
);

CREATE INDEX IF NOT EXISTS idx_jd ON observations(jd);
CREATE INDEX IF NOT EXISTS idx_calendar_date ON observations(calendar_date);
CREATE INDEX IF NOT EXISTS idx_star ON observations(star);
```

### 2. Corrigir migrate_to_d1.py
```python
# Query correta
cursor.execute("""
    SELECT
        star,
        jd,              # ✅ Correto
        calendar_date,   # ✅ Correto
        magnitude,
        error,
        band,            # ⚠️ Será mapeado para "filter" no INSERT
        observer
    FROM observations
    ORDER BY id
""")

# INSERT corrigido
sql = """
INSERT OR IGNORE INTO observations 
(star, jd, calendar_date, magnitude, error, filter, observer, scraped_at) 
VALUES ...
"""
```

### 3. Adicionar campo scraped_at
O D1 tem o campo `scraped_at` que não existe no SQLite local. Opções:
- Usar `created_at` do SQLite como `scraped_at`
- Deixar NULL
- Usar data atual da migração

## 📝 Mapeamento de Colunas

| SQLite Local | D1 Real | Ação |
|--------------|---------|------|
| `star` | `star` | ✅ Direto |
| `jd` | `jd` | ✅ Direto |
| `calendar_date` | `calendar_date` | ✅ Direto |
| `magnitude` | `magnitude` | ✅ Direto (converter REAL→TEXT) |
| `error` | `error` | ✅ Direto (converter REAL→TEXT) |
| `band` | `filter` | ⚠️ Renomear |
| `observer` | `observer` | ✅ Direto |
| `created_at` | `scraped_at` | ⚠️ Mapear |
| `created_at` | `created_at` | ✅ Direto |

## 🎯 Plano de Ação

1. ✅ Atualizar `schema_d1.sql` com schema correto
2. ✅ Corrigir `migrate_to_d1.py`:
   - Query SELECT com colunas corretas
   - INSERT com mapeamento correto
   - Adicionar `scraped_at`
3. ✅ Testar migração com amostra pequena
4. ✅ Executar migração completa