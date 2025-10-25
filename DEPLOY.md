# Guia de Deploy - Cloudflare Workers

Este guia explica como fazer o deploy do sistema de monitoramento T CrB na Cloudflare Workers.

## Pré-requisitos

1. Conta na Cloudflare (gratuita)
2. Node.js instalado
3. Wrangler CLI instalado

## Instalação do Wrangler

```bash
npm install -g wrangler
```

## Autenticação

```bash
wrangler login
```

## Configuração do Projeto

1. Copie o arquivo de exemplo:
```bash
cp wrangler.toml.example wrangler.toml
```

2. Edite `wrangler.toml` e ajuste o nome do projeto se necessário.

## Criando o Banco de Dados D1 (Opcional)

Se você quiser usar o banco de dados D1 da Cloudflare:

```bash
# Criar o banco de dados
wrangler d1 create tcrb-observations

# Copie o database_id retornado e adicione ao wrangler.toml
```

Crie a tabela no banco:

```bash
wrangler d1 execute tcrb-observations --command "
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
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_jd ON observations(jd);
CREATE INDEX idx_calendar_date ON observations(calendar_date);
"
```

## Deploy

### Deploy de Desenvolvimento

```bash
wrangler deploy --env development
```

### Deploy de Produção

```bash
wrangler deploy
```

## Testando o Worker

Após o deploy, você pode testar o worker:

```bash
# Testar via HTTP
curl https://tcrb-monitoring.seu-usuario.workers.dev

# Ver logs
wrangler tail
```

## Configuração do Cron

O cron já está configurado no `wrangler.toml` para executar a cada hora:
```
crons = ["0 * * * *"]
```

Você pode ajustar a frequência conforme necessário:
- `*/30 * * * *` - A cada 30 minutos
- `0 */2 * * *` - A cada 2 horas
- `0 0 * * *` - Uma vez por dia à meia-noite

## Monitoramento

Você pode monitorar as execuções do worker no dashboard da Cloudflare:
1. Acesse https://dash.cloudflare.com
2. Vá em Workers & Pages
3. Selecione seu worker
4. Veja logs e métricas

## Custos

O plano gratuito da Cloudflare Workers inclui:
- 100.000 requisições por dia
- 10ms de CPU por requisição
- Cron Triggers ilimitados

Para este projeto, o plano gratuito é mais do que suficiente.

## Troubleshooting

### Erro de autenticação
```bash
wrangler logout
wrangler login
```

### Ver logs em tempo real
```bash
wrangler tail --format pretty
```

### Testar localmente
```bash
wrangler dev
```

## Próximos Passos

1. Configure alertas no Cloudflare para ser notificado de erros
2. Configure um webhook para enviar notificações quando houver novas observações
3. Crie um dashboard para visualizar os dados coletados