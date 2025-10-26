# Guia de Instalação - T CrB Monitoring

## Pré-requisitos

### 1. Instalar Python 3.8+

Verifique se o Python está instalado:
```bash
python3 --version
```

Se não estiver instalado:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Fedora
sudo dnf install python3 python3-pip

# macOS (com Homebrew)
brew install python3
```

### 2. Instalar PostgreSQL

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# Fedora
sudo dnf install postgresql-server postgresql-contrib

# macOS
brew install postgresql
```

## Instalação do Projeto

### 1. Clone o repositório

```bash
git clone https://github.com/cosmicpb/tcrbmonitoring.git
cd tcrbmonitoring
```

### 2. Crie um ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

Se o pip não estiver disponível:
```bash
# Ubuntu/Debian
sudo apt install python3-pip

# Ou instale manualmente
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
```

### 4. Configure o PostgreSQL

```bash
# Inicie o serviço PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Acesse o PostgreSQL
sudo -u postgres psql

# No prompt do PostgreSQL, crie o banco e usuário:
CREATE DATABASE tcrb_monitoring;
CREATE USER tcrb_user WITH PASSWORD 'sua_senha_segura';
GRANT ALL PRIVILEGES ON DATABASE tcrb_monitoring TO tcrb_user;
\q
```

### 5. Configure as variáveis de ambiente

```bash
cp .env.example .env
nano .env  # ou use seu editor preferido
```

Edite o arquivo `.env`:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tcrb_monitoring
DB_USER=tcrb_user
DB_PASSWORD=sua_senha_segura
```

### 6. Teste a instalação

```bash
# Teste o scraper
python3 scraper.py

# Teste o banco de dados
python3 database.py

# Execute uma coleta completa
python3 monitor.py
```

## Execução

### Coleta única

```bash
python3 monitor.py
```

### Monitoramento contínuo (a cada hora)

```bash
python3 scheduler.py
```

## Automação com Systemd (Linux)

### 1. Crie o arquivo de serviço

```bash
sudo nano /etc/systemd/system/tcrb-monitor.service
```

Conteúdo:
```ini
[Unit]
Description=T CrB Monitoring Service
After=network.target postgresql.service

[Service]
Type=simple
User=seu_usuario
WorkingDirectory=/caminho/completo/para/tcrbmonitoring
Environment="PATH=/caminho/completo/para/tcrbmonitoring/venv/bin"
ExecStart=/caminho/completo/para/tcrbmonitoring/venv/bin/python scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Ative e inicie o serviço

```bash
sudo systemctl daemon-reload
sudo systemctl enable tcrb-monitor
sudo systemctl start tcrb-monitor
sudo systemctl status tcrb-monitor
```

### 3. Ver logs

```bash
sudo journalctl -u tcrb-monitor -f
```

## Automação com Cron (Alternativa)

```bash
crontab -e
```

Adicione:
```
0 * * * * cd /caminho/para/tcrbmonitoring && /caminho/para/venv/bin/python monitor.py >> /var/log/tcrb.log 2>&1
```

## Troubleshooting

### Erro: "No module named pip"

```bash
sudo apt install python3-pip
# ou
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
```

### Erro: "psycopg2 installation failed"

```bash
# Instale as dependências de desenvolvimento
sudo apt install libpq-dev python3-dev
pip install psycopg2-binary
```

### Erro: "Connection refused" (PostgreSQL)

```bash
# Verifique se o PostgreSQL está rodando
sudo systemctl status postgresql

# Inicie se necessário
sudo systemctl start postgresql

# Verifique as configurações de conexão no .env
```

### Erro: "Permission denied" (PostgreSQL)

```bash
# Verifique as permissões do usuário
sudo -u postgres psql
GRANT ALL PRIVILEGES ON DATABASE tcrb_monitoring TO tcrb_user;
\q
```

## Deploy na Cloudflare

Consulte o arquivo `README.md` para instruções de deploy na Cloudflare Workers.

## Suporte

Para problemas ou dúvidas, abra uma issue no GitHub:
https://github.com/cosmicpb/tcrbmonitoring/issues