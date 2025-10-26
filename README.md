# T CrB Monitoring

Sistema de monitoramento automático da estrela variável T Coronae Borealis (T CrB) através do portal AAVSO.

## 🌟 Sobre

Este projeto realiza web scraping periódico dos dados de magnitude da estrela T CrB, armazenando as observações em um banco de dados PostgreSQL. O sistema executa automaticamente a cada hora para coletar novos dados.

### Por que T CrB?

T Coronae Borealis é uma estrela variável do tipo nova recorrente, conhecida por suas erupções espetaculares que aumentam seu brilho em até 10 magnitudes. O monitoramento contínuo é crucial para detectar o início de uma nova erupção.

## 📊 Dados Coletados

Para cada observação, são extraídos:
- **Star**: Nome da estrela (T CrB)
- **JD**: Data Juliana (Julian Date)
- **Calendar Date**: Data no formato de calendário
- **Magnitude**: Magnitude observada
- **Error**: Margem de erro da medição
- **Filter**: Filtro utilizado
- **Observer**: Código do observador
- **Scraped At**: Timestamp da coleta

## 🚀 Instalação

### Pré-requisitos

- Python 3.8+
- PostgreSQL 12+

### Passos

1. Clone o repositório:
```bash
git clone https://github.com/cosmicpb/tcrbmonitoring.git
cd tcrbmonitoring
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure o banco de dados:
```bash
# Crie o banco no PostgreSQL
createdb tcrb_monitoring

# Copie e configure o arquivo .env
cp .env.example .env
# Edite .env com suas credenciais
```

## 💻 Uso

### Executar uma coleta única

```bash
python monitor.py
```

### Executar monitoramento contínuo (a cada hora)

```bash
python scheduler.py
```

### Testar apenas o scraper

```bash
python scraper.py
```

### Verificar banco de dados

```bash
python database.py
```

## 🗄️ Banco de Dados

### Estrutura da Tabela

```sql
CREATE TABLE observations (
    id SERIAL PRIMARY KEY,
    star VARCHAR(50) NOT NULL,
    jd VARCHAR(50) NOT NULL UNIQUE,
    calendar_date VARCHAR(100) NOT NULL,
    magnitude VARCHAR(50) NOT NULL,
    error VARCHAR(50),
    filter VARCHAR(50) NOT NULL,
    observer VARCHAR(50) NOT NULL,
    scraped_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Consultas Úteis

```sql
-- Total de observações
SELECT COUNT(*) FROM observations;

-- Últimas 10 observações
SELECT * FROM observations ORDER BY jd DESC LIMIT 10;

-- Observações por filtro
SELECT filter, COUNT(*) FROM observations GROUP BY filter;

-- Magnitude média (excluindo limites superiores)
SELECT AVG(CAST(magnitude AS FLOAT)) 
FROM observations 
WHERE magnitude NOT LIKE '%<%';
```

## ☁️ Deploy na Cloudflare

### Usando Cloudflare Workers + D1

1. Instale Wrangler:
```bash
npm install -g wrangler
```

2. Faça login:
```bash
wrangler login
```

3. Crie banco D1:
```bash
wrangler d1 create tcrb-observations
```

4. Configure wrangler.toml com o database_id retornado

5. Crie a tabela:
```bash
wrangler d1 execute tcrb-observations --file=schema.sql
```

6. Deploy:
```bash
wrangler deploy
```

### Usando Cloudflare Workers + PostgreSQL Externo

Configure a connection string no wrangler.toml:
```toml
[vars]
DATABASE_URL = "postgresql://user:pass@host:port/db"
```

## 🔄 Automação

### Usando Cron (Linux/Mac)

```bash
# Editar crontab
crontab -e

# Adicionar linha para executar a cada hora
0 * * * * cd /path/to/tcrbmonitoring && /path/to/venv/bin/python monitor.py >> /var/log/tcrb.log 2>&1
```

### Usando Systemd (Linux)

Crie `/etc/systemd/system/tcrb-monitor.service`:

```ini
[Unit]
Description=T CrB Monitoring Service
After=network.target postgresql.service

[Service]
Type=simple
User=seu_usuario
WorkingDirectory=/path/to/tcrbmonitoring
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python scheduler.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Ative o serviço:
```bash
sudo systemctl enable tcrb-monitor
sudo systemctl start tcrb-monitor
sudo systemctl status tcrb-monitor
```

## 📈 Exemplo de Saída

```
============================================================
T CrB Monitoring System
============================================================
Buscando dados de https://apps.aavso.org/webobs/results/...
✓ Dados extraídos: T CRB - Magnitude: 9.9
✓ Conectado ao banco de dados PostgreSQL
✓ Tabelas criadas/verificadas com sucesso
✓ Nova observação salva com sucesso!
   ID: 42
   JD: 2460974.152
   Data: 2025 Oct. 25.65200
   Magnitude: 9.9

📊 Total de observações: 42
```

## 🛠️ Tecnologias

- **Python 3.8+**
- **BeautifulSoup4** - Parsing HTML
- **Requests** - HTTP requests
- **PostgreSQL** - Banco de dados
- **psycopg2** - Driver PostgreSQL
- **schedule** - Agendamento de tarefas
- **python-dotenv** - Gerenciamento de variáveis de ambiente

## 📝 Licença

MIT

## 🤝 Contribuindo

Contribuições são bem-vindas! Abra uma issue ou pull request.

## 📧 Contato

Para dúvidas ou sugestões, abra uma issue no repositório.

## 🌐 Fonte dos Dados

Dados coletados do portal oficial da AAVSO:
https://apps.aavso.org/webobs/results/?star=t+crb