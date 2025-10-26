# Guia Rápido - T CrB Monitoring

## Configuração do Banco de Dados (5 minutos)

### Passo 1: Execute o script SQL

Abra um terminal e execute:

```bash
sudo -u postgres psql -f setup_database.sql
```

**OU** execute manualmente:

```bash
# Entre no PostgreSQL como usuário postgres
sudo -u postgres psql

# Dentro do psql, execute:
CREATE DATABASE tcrb_monitoring;
\c tcrb_monitoring
CREATE USER tcrb_user WITH PASSWORD 'tcrb_password_123';
GRANT ALL PRIVILEGES ON DATABASE tcrb_monitoring TO tcrb_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO tcrb_user;

# Saia do psql
\q
```

### Passo 2: Crie as tabelas

```bash
sudo -u postgres psql -d tcrb_monitoring -f schema.sql
```

**OU** use o Python:

```bash
./venv/bin/python database.py
```

### Passo 3: Teste a conexão

```bash
./venv/bin/python database.py
```

Você deve ver:
```
✓ Conectado ao banco de dados PostgreSQL
✓ Tabelas criadas/verificadas com sucesso
```

## Executar o Monitoramento

### Coleta única:

```bash
./venv/bin/python monitor.py
```

### Monitoramento contínuo (a cada hora):

```bash
./venv/bin/python scheduler.py
```

## Consultar o Banco de Dados

### Via psql:

```bash
# Conectar ao banco
psql -h localhost -U tcrb_user -d tcrb_monitoring

# Dentro do psql:
# Ver todas as observações
SELECT * FROM observations ORDER BY jd DESC LIMIT 10;

# Contar observações
SELECT COUNT(*) FROM observations;

# Ver estatísticas
SELECT 
    COUNT(*) as total,
    MIN(calendar_date) as primeira,
    MAX(calendar_date) as ultima,
    MAX(magnitude) as mag_max
FROM observations;

# Sair
\q
```

### Via Python:

```bash
./venv/bin/python database.py
```

### Via código Python:

```python
from database import Database

db = Database()
db.connect()

# Ver últimas 10 observações
obs = db.get_latest_observations(10)
for o in obs:
    print(f"{o['calendar_date']}: {o['magnitude']}")

# Ver estatísticas
stats = db.get_stats()
print(f"Total: {stats['total']}")

db.disconnect()
```

## Queries Úteis

```sql
-- Total de observações
SELECT COUNT(*) FROM observations;

-- Últimas 20 observações
SELECT id, calendar_date, magnitude, filter, observer 
FROM observations 
ORDER BY jd DESC 
LIMIT 20;

-- Observações por filtro
SELECT filter, COUNT(*) as total 
FROM observations 
GROUP BY filter 
ORDER BY total DESC;

-- Observações por observador
SELECT observer, COUNT(*) as total 
FROM observations 
GROUP BY observer 
ORDER BY total DESC 
LIMIT 10;

-- Magnitude média (excluindo limites superiores)
SELECT AVG(CAST(magnitude AS FLOAT)) as media
FROM observations 
WHERE magnitude NOT LIKE '%<%' 
  AND magnitude ~ '^[0-9.]+$';

-- Observações de hoje
SELECT * FROM observations 
WHERE created_at::date = CURRENT_DATE 
ORDER BY jd DESC;

-- Buscar por data específica
SELECT * FROM observations 
WHERE calendar_date LIKE '%2025 Oct. 25%' 
ORDER BY jd DESC;
```

## Troubleshooting

### Erro: "connection refused"

```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Iniciar se necessário
sudo systemctl start postgresql
```

### Erro: "password authentication failed"

Verifique o arquivo `.env` e certifique-se de que a senha está correta.

### Erro: "permission denied"

```bash
# Conceder permissões novamente
sudo -u postgres psql -d tcrb_monitoring -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tcrb_user;"
sudo -u postgres psql -d tcrb_monitoring -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tcrb_user;"
```

## Automação

### Executar a cada hora com cron:

```bash
crontab -e
```

Adicione:
```
0 * * * * cd /caminho/para/tcrbmonitoring && ./venv/bin/python monitor.py >> /var/log/tcrb.log 2>&1
```

### Ou use systemd (ver INSTALL.md)

## Backup do Banco

```bash
# Backup
pg_dump -h localhost -U tcrb_user tcrb_monitoring > backup.sql

# Restaurar
psql -h localhost -U tcrb_user tcrb_monitoring < backup.sql
```

## Próximos Passos

1. ✅ Configure o banco de dados
2. ✅ Execute o monitor
3. ✅ Verifique os dados no banco
4. ✅ Configure automação (cron ou systemd)
5. 🚀 Deploy na Cloudflare (opcional)