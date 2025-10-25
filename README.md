# T CrB Monitoring

Sistema de monitoramento de observações da estrela variável T CrB (T Coronae Borealis) através do portal da AAVSO (American Association of Variable Star Observers).

## 🌟 Sobre o Projeto

Este projeto realiza web scraping periódico dos dados de magnitude da estrela T CrB, armazenando as observações mais recentes em um banco de dados SQLite. O sistema está preparado para deploy na Cloudflare Workers para execução automatizada na nuvem.

### Por que T CrB?

T Coronae Borealis é uma estrela variável do tipo nova recorrente, conhecida por suas erupções espetaculares que aumentam seu brilho em até 10 magnitudes. O monitoramento contínuo é crucial para detectar o início de uma nova erupção.

## 📊 Dados Coletados

Para cada observação, são extraídos os seguintes campos:
- **Star**: Nome da estrela (T CrB)
- **JD**: Data Juliana (Julian Date)
- **Calendar Date**: Data no formato de calendário
- **Magnitude**: Magnitude observada da estrela
- **Error**: Margem de erro da medição
- **Filter**: Filtro utilizado na observação
- **Observer**: Código do observador
- **Timestamp**: Data/hora da coleta dos dados

## 📁 Estrutura do Projeto

```
tcrbmonitoring/
├── src/
│   ├── scraper.js      # Script principal de scraping
│   ├── database.js     # Gerenciamento do banco SQLite
│   ├── index.js        # Ponto de entrada principal
│   ├── scheduler.js    # Execução periódica local
│   ├── worker.js       # Worker para Cloudflare
│   ├── view-data.js    # Visualizador de dados
│   └── test.js         # Testes
├── data/
│   ├── observations.db  # Banco de dados SQLite
│   └── observations.csv # Backup em CSV
├── package.json
├── wrangler.toml.example # Configuração Cloudflare
├── DEPLOY.md           # Guia de deploy
├── .gitignore
└── README.md
```

## 🚀 Instalação

1. Clone o repositório:
```bash
git clone <seu-repositorio>
cd tcrbmonitoring
```

2. Instale as dependências:
```bash
npm install
```

## 💻 Uso Local

### Executar uma coleta única:
```bash
npm run dev
```

### Executar apenas o scraper (sem banco):
```bash
npm run scrape
```

### Executar testes:
```bash
npm run test
```

### Visualizar dados coletados:
```bash
npm run view
```

### Exportar dados para CSV:
```bash
npm run export
```

### Executar monitoramento periódico (a cada hora):
```bash
npm start
```

## 🗄️ Banco de Dados

O sistema usa SQLite para armazenar as observações localmente. O banco é criado automaticamente em `data/observations.db` na primeira execução.

### Estrutura da Tabela

```sql
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
```

## ☁️ Deploy na Cloudflare Workers

Para deploy na Cloudflare Workers com execução periódica automatizada, consulte o guia completo em [`DEPLOY.md`](DEPLOY.md:1).

### Resumo rápido:

1. Instale o Wrangler CLI:
```bash
npm install -g wrangler
```

2. Faça login:
```bash
wrangler login
```

3. Configure o projeto:
```bash
cp wrangler.toml.example wrangler.toml
```

4. Faça o deploy:
```bash
wrangler deploy
```

O worker será executado automaticamente a cada hora via Cron Triggers.

## 📈 Exemplo de Saída

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

## 🔍 Visualização de Dados

```
=== Visualizador de Dados T CrB ===

📊 Estatísticas:
   Total de observações: 1
   Última observação: 2025 Oct. 25.65200
   Magnitude atual: <4.9

📋 Últimas 10 observações:
────────────────────────────────────────────────────────────────────
ID  | JD           | Data              | Magnitude | Filtro | Observador
────────────────────────────────────────────────────────────────────
1   | 2460974.152  | 2025 Oct. 25.65200| <4.9      | Vis.   | MQA
────────────────────────────────────────────────────────────────────
```

## 🌐 Fonte dos Dados

Os dados são coletados do portal oficial da AAVSO:
https://apps.aavso.org/webobs/results/?star=t+crb

## 🛠️ Tecnologias Utilizadas

- **Node.js** - Runtime JavaScript
- **Cheerio** - Parser HTML para web scraping
- **Better-SQLite3** - Banco de dados SQLite
- **Cloudflare Workers** - Plataforma serverless para deploy
- **Cloudflare D1** - Banco de dados SQL na nuvem (opcional)

## 📝 Licença

MIT

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

## 📧 Contato

Para dúvidas ou sugestões, abra uma issue no repositório.