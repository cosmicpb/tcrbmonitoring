# Deploy na Cloudflare Workers com D1 Database

Guia completo para fazer deploy do sistema T CrB Monitoring na Cloudflare.

## Pré-requisitos

- Conta na Cloudflare (gratuita)
- Wrangler CLI instalado
- Node.js 20+ (já instalado)

## Passo 1: Criar o Banco D1

```bash
# Criar banco D1
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 create tcrb-observations"
```

Você receberá uma saída como:
```
✅ Successfully created DB 'tcrb-observations'

[[d1_databases]]
binding = "DB"
database_name = "tcrb-observations"
database_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

**Copie o `database_id`!**

## Passo 2: Configurar wrangler.toml

Edite o arquivo `wrangler.toml` e descomente as linhas do D1:

```toml
[[d1_databases]]
binding = "DB"
database_name = "tcrb-observations"
database_id = "cole-seu-database-id-aqui"
```

## Passo 3: Criar Tabelas no D1

```bash
# Criar tabelas
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --file=schema.sql"
```

Ou crie manualmente:

```bash
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --command=\"
CREATE TABLE observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    star TEXT NOT NULL,
    jd TEXT NOT NULL UNIQUE,
    calendar_date TEXT NOT NULL,
    magnitude TEXT NOT NULL,
    error TEXT,
    filter TEXT NOT NULL,
    observer TEXT NOT NULL,
    scraped_at TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_jd ON observations(jd);
CREATE INDEX idx_calendar_date ON observations(calendar_date);
CREATE INDEX idx_created_at ON observations(created_at);
\""
```

## Passo 4: Fazer Deploy

```bash
# Deploy do worker
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler deploy"
```

Você receberá uma URL como:
```
https://tcrb-monitoring.seu-usuario.workers.dev
```

## Passo 5: Verificar Funcionamento

### Testar via HTTP:

```bash
curl https://tcrb-monitoring.seu-usuario.workers.dev
```

Você deve receber um JSON com os dados mais recentes.

### Ver logs em tempo real:

```bash
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler tail"
```

## Passo 6: Verificar Cron

O cron já está configurado para executar a cada hora (`0 * * * *`).

Para verificar:
1. Acesse https://dash.cloudflare.com
2. Vá em "Workers & Pages"
3. Clique em "tcrb-monitoring"
4. Veja a aba "Triggers" - deve mostrar o cron configurado

## Consultar Dados no D1

### Via Wrangler:

```bash
# Listar todas as observações
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --command='SELECT * FROM observations ORDER BY jd DESC LIMIT 10'"

# Contar observações
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --command='SELECT COUNT(*) as total FROM observations'"

# Ver estatísticas
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --command='SELECT COUNT(*) as total, MIN(calendar_date) as primeira, MAX(calendar_date) as ultima FROM observations'"
```

### Via Dashboard:

1. Acesse https://dash.cloudflare.com
2. Vá em "Workers & Pages"
3. Clique em "D1"
4. Selecione "tcrb-observations"
5. Use a aba "Console" para executar queries SQL

## Monitoramento

### Ver logs:

```bash
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler tail --format pretty"
```

### Ver métricas:

1. Acesse https://dash.cloudflare.com
2. Vá em "Workers & Pages"
3. Clique em "tcrb-monitoring"
4. Veja métricas de execução, erros, etc.

## Custos

### Plano Gratuito Inclui:

- **Workers**: 100.000 requisições/dia
- **D1**: 5 GB de armazenamento
- **Cron Triggers**: Ilimitados
- **Execuções**: 10ms de CPU por requisição

Para este projeto, o plano gratuito é mais do que suficiente!

## Troubleshooting

### Erro: "Python Workers not supported"

Certifique-se de que o `wrangler.toml` tem:
```toml
compatibility_flags = ["python_workers"]
```

### Erro: "Database not found"

Verifique se o `database_id` no `wrangler.toml` está correto.

### Erro: "Table doesn't exist"

Execute novamente o script de criação de tabelas:
```bash
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --file=schema.sql"
```

### Ver logs detalhados:

```bash
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler tail --format json"
```

## Atualizar o Worker

Após fazer mudanças no código:

```bash
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler deploy"
```

## Backup do D1

```bash
# Exportar dados
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 export tcrb-observations --output=backup.sql"

# Importar dados
bash -c "source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations --file=backup.sql"
```

## Scripts Úteis

Adicione ao `package.json`:

```json
{
  "scripts": {
    "deploy": "bash -c 'source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler deploy'",
    "tail": "bash -c 'source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler tail'",
    "d1:query": "bash -c 'source ~/.nvm/nvm.sh && nvm use 20 && npx wrangler d1 execute tcrb-observations'"
  }
}
```

Uso:
```bash
npm run deploy
npm run tail
```

## Próximos Passos

1. ✅ Criar banco D1
2. ✅ Configurar wrangler.toml
3. ✅ Criar tabelas
4. ✅ Fazer deploy
5. ✅ Verificar cron
6. 🎉 Sistema rodando automaticamente na nuvem!

O worker executará automaticamente a cada hora e coletará os dados mais recentes da estrela T CrB!