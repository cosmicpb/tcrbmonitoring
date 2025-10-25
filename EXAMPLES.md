# Exemplos de Uso

Este documento contém exemplos práticos de como usar o sistema de monitoramento T CrB.

## 1. Primeira Execução

```bash
# Instalar dependências
npm install

# Executar teste para verificar se está funcionando
npm run test

# Fazer primeira coleta de dados
npm run dev
```

**Saída esperada:**
```
=== T CrB Monitoring System ===
Iniciado em: 25/10/2025, 20:43:29

Banco de dados inicializado: /path/to/observations.db
Buscando dados da AAVSO...
✓ Nova observação registrada no banco de dados (ID: 1)

Estatísticas: 1 observações no banco
Última magnitude: <4.9

Resultado: saved
```

## 2. Visualizar Dados Coletados

```bash
npm run view
```

**Saída:**
```
=== Visualizador de Dados T CrB ===

📊 Estatísticas:
   Total de observações: 5
   Última observação: 2025 Oct. 25.65200
   Magnitude atual: <4.9
   Primeira observação: 2025 Oct. 24.50000

📋 Últimas 10 observações:
────────────────────────────────────────────────────────────────────
ID  | JD           | Data              | Magnitude | Filtro | Observador
────────────────────────────────────────────────────────────────────
5   | 2460974.152  | 2025 Oct. 25.65200| <4.9      | Vis.   | MQA
4   | 2460973.620  | 2025 Oct. 25.12083| 9.9       | Vis.   | SBRE
3   | 2460973.618  | 2025 Oct. 25.11875| 9.6       | Vis.   | BALQ
2   | 2460973.573  | 2025 Oct. 25.07325| 10.9599   | B      | WGR
1   | 2460973.500  | 2025 Oct. 24.50000| 9.968     | V      | UJHA
────────────────────────────────────────────────────────────────────
```

## 3. Exportar Dados para CSV

```bash
npm run export
```

Isso criará um arquivo `data/export.csv` com todos os dados do banco.

## 4. Monitoramento Contínuo Local

Para executar o monitoramento a cada hora automaticamente:

```bash
npm start
```

**Saída:**
```
🚀 T CrB Monitoring Scheduler Iniciado
⏰ Intervalo de execução: 60 minutos
📅 Iniciado em: 25/10/2025, 20:00:00

Pressione Ctrl+C para parar

================================================================================
Execução #1 - 25/10/2025, 20:00:00
================================================================================
=== T CrB Monitoring System ===
Iniciado em: 25/10/2025, 20:00:00

Banco de dados inicializado: /path/to/observations.db
Buscando dados da AAVSO...
✓ Observação já registrada no banco de dados.

Estatísticas: 5 observações no banco

Resultado: duplicate
ℹ️  Nenhuma nova observação disponível
Próxima execução em 60 minutos...
```

## 5. Integração com Cron (Linux/Mac)

Para executar automaticamente no sistema, adicione ao crontab:

```bash
# Editar crontab
crontab -e

# Adicionar linha para executar a cada hora
0 * * * * cd /path/to/tcrbmonitoring && /usr/bin/npm run dev >> /path/to/logs/tcrb.log 2>&1
```

## 6. Consultas SQL Personalizadas

Você pode fazer consultas personalizadas no banco de dados:

```bash
# Instalar sqlite3 CLI (se não tiver)
sudo apt-get install sqlite3  # Ubuntu/Debian
brew install sqlite3          # macOS

# Abrir o banco
sqlite3 data/observations.db

# Exemplos de consultas
sqlite> SELECT COUNT(*) FROM observations;
sqlite> SELECT * FROM observations ORDER BY jd DESC LIMIT 5;
sqlite> SELECT AVG(CAST(magnitude AS REAL)) FROM observations WHERE magnitude NOT LIKE '%<%';
sqlite> SELECT calendar_date, magnitude FROM observations WHERE CAST(magnitude AS REAL) < 5;
```

## 7. Análise de Dados com Python

Exemplo de script Python para análise:

```python
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# Conectar ao banco
conn = sqlite3.connect('data/observations.db')

# Ler dados
df = pd.read_sql_query("SELECT * FROM observations", conn)

# Converter magnitude para numérico (ignorando valores com '<')
df['magnitude_numeric'] = pd.to_numeric(df['magnitude'].str.replace('<', ''), errors='coerce')

# Plotar curva de luz
plt.figure(figsize=(12, 6))
plt.plot(df['jd'], df['magnitude_numeric'], 'o-')
plt.xlabel('Julian Date')
plt.ylabel('Magnitude')
plt.title('T CrB Light Curve')
plt.gca().invert_yaxis()  # Magnitudes menores = mais brilhante
plt.grid(True)
plt.savefig('light_curve.png')
plt.show()

conn.close()
```

## 8. Webhook para Notificações

Exemplo de como adicionar notificações via webhook (Discord, Slack, etc.):

Edite `src/index.js` e adicione após salvar nova observação:

```javascript
// Enviar notificação via webhook
if (result.success) {
  const webhookUrl = 'https://discord.com/api/webhooks/...';
  
  await fetch(webhookUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      content: `🌟 Nova observação T CrB!\nMagnitude: ${data.magnitude}\nData: ${data.calendarDate}`
    })
  });
}
```

## 9. Deploy na Cloudflare

```bash
# Instalar Wrangler
npm install -g wrangler

# Login
wrangler login

# Configurar
cp wrangler.toml.example wrangler.toml

# Deploy
wrangler deploy

# Ver logs
wrangler tail
```

## 10. Backup dos Dados

```bash
# Backup do banco de dados
cp data/observations.db data/observations.db.backup

# Ou exportar para CSV
npm run export

# Backup automático diário (adicionar ao crontab)
0 0 * * * cp /path/to/tcrbmonitoring/data/observations.db /path/to/backups/observations-$(date +\%Y\%m\%d).db
```

## Dicas

1. **Monitoramento de Erros**: Configure alertas para ser notificado se o scraping falhar
2. **Análise de Tendências**: Use os dados coletados para identificar padrões na variabilidade
3. **Compartilhamento**: Exporte os dados e compartilhe com a comunidade astronômica
4. **Automação**: Configure o sistema para rodar automaticamente e esqueça!

## Troubleshooting

### Erro: "SQLITE_CONSTRAINT_UNIQUE"
Isso significa que a observação já existe no banco. É normal e esperado.

### Erro: "Failed to fetch"
Verifique sua conexão com a internet e se o site da AAVSO está acessível.

### Banco de dados corrompido
```bash
# Fazer backup
cp data/observations.db data/observations.db.old

# Recriar banco
rm data/observations.db
npm run dev