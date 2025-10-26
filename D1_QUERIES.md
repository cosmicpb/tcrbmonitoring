# Guia de Consultas ao D1 Database

## Consultar Dados Remotos

**IMPORTANTE**: Sempre use `--remote` para consultar o banco de dados na nuvem!

## Queries Básicas

### Ver todas as observações (últimas 10)

```bash
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --remote --command='SELECT * FROM observations ORDER BY jd DESC LIMIT 10'"
```

### Contar total de observações

```bash
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --remote --command='SELECT COUNT(*) as total FROM observations'"
```

### Ver última observação

```bash
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --remote --command='SELECT * FROM observations ORDER BY jd DESC LIMIT 1'"
```

### Estatísticas gerais

```bash
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --remote --command='SELECT COUNT(*) as total, MIN(calendar_date) as primeira, MAX(calendar_date) as ultima, MAX(magnitude) as mag_max FROM observations'"
```

## Queries Avançadas

### Observações por filtro

```bash
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --remote --command='SELECT filter, COUNT(*) as total FROM observations GROUP BY filter ORDER BY total DESC'"
```

### Observações por observador (top 10)

```bash
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --remote --command='SELECT observer, COUNT(*) as total FROM observations GROUP BY observer ORDER BY total DESC LIMIT 10'"
```

### Observações de hoje

```bash
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --remote --command='SELECT * FROM observations WHERE DATE(created_at) = DATE(\"now\") ORDER BY jd DESC'"
```

### Buscar por data específica

```bash
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --remote --command='SELECT * FROM observations WHERE calendar_date LIKE \"%2025 Oct. 25%\" ORDER BY jd DESC'"
```

### Últimas 50 observações com magnitude

```bash
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --remote --command='SELECT jd, calendar_date, magnitude, filter, observer FROM observations ORDER BY jd DESC LIMIT 50'"
```

## Via Dashboard da Cloudflare

1. Acesse: https://dash.cloudflare.com
2. Vá em **Workers & Pages**
3. Clique em **D1**
4. Selecione **tcrb-observations**
5. Use a aba **Console** para executar queries SQL diretamente

Exemplos de queries no console:

```sql
-- Ver todas as observações
SELECT * FROM observations ORDER BY jd DESC LIMIT 20;

-- Contar total
SELECT COUNT(*) as total FROM observations;

-- Estatísticas
SELECT 
    COUNT(*) as total,
    MIN(calendar_date) as primeira_obs,
    MAX(calendar_date) as ultima_obs
FROM observations;

-- Por filtro
SELECT filter, COUNT(*) as quantidade 
FROM observations 
GROUP BY filter 
ORDER BY quantidade DESC;

-- Últimas 10 com detalhes
SELECT 
    id,
    calendar_date,
    magnitude,
    filter,
    observer,
    created_at
FROM observations 
ORDER BY jd DESC 
LIMIT 10;
```

## Exportar Dados

### Exportar para arquivo SQL

```bash
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 export tcrb-observations --remote --output=backup.sql"
```

### Exportar query específica para JSON

```bash
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --remote --json --command='SELECT * FROM observations ORDER BY jd DESC LIMIT 100'" > observations.json
```

## Inserir Dados Manualmente (se necessário)

```bash
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --remote --command='INSERT INTO observations (star, jd, calendar_date, magnitude, error, filter, observer, scraped_at) VALUES (\"T CRB\", \"2460974.152\", \"2025 Oct. 25.65200\", \"<4.9\", \"—\", \"Vis.\", \"MQA\", \"2025-10-26T02:00:00Z\")'"
```

## Limpar Dados (CUIDADO!)

```bash
# Deletar todas as observações (USE COM CUIDADO!)
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --remote --command='DELETE FROM observations'"

# Deletar observações específicas
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --remote --command='DELETE FROM observations WHERE jd = \"2460974.152\"'"
```

## Verificar Estrutura da Tabela

```bash
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --remote --command='PRAGMA table_info(observations)'"
```

## Dicas

1. **Sempre use `--remote`** para consultar o banco na nuvem
2. **Use `--json`** para obter saída em formato JSON
3. **Escape aspas** dentro do comando SQL com `\"`
4. **Limite resultados** com `LIMIT` para evitar muitos dados
5. **Use o Dashboard** para queries interativas

## Troubleshooting

### Erro: "no such table"
- Certifique-se de usar `--remote`
- Verifique se as tabelas foram criadas com o schema.sql

### Erro: "database not found"
- Verifique o database_id no wrangler.toml
- Confirme que está logado: `npx wrangler login`

### Nenhum dado retornado
- O cron ainda não executou (aguarde até a próxima hora cheia)
- Ou insira dados manualmente para testar