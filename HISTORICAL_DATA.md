# Coleta de Dados Históricos - T CrB

Este documento explica como coletar todos os dados históricos da estrela T CrB do portal AAVSO.

## Script de Coleta

O script [`historical_scraper.py`](historical_scraper.py) foi criado para coletar automaticamente todos os dados históricos disponíveis no AAVSO.

### Características

- ✅ Coleta dados de todas as páginas automaticamente (até 3600 páginas)
- ✅ Converte datas para formato brasileiro (dd/MM/YYYY HH:mm)
- ✅ Salva dados no banco SQLite local
- ✅ Evita duplicatas automaticamente
- ✅ Mostra progresso em tempo real
- ✅ Respeita o servidor com delay entre requisições
- ✅ Pode ser interrompido e retomado (ignora duplicatas)

### Requisitos

```bash
pip install requests beautifulsoup4
```

### Como Usar

1. **Execute o script:**

```bash
python3 historical_scraper.py
```

2. **O script irá:**
   - Descobrir quantas páginas existem (~3600 páginas)
   - Estimar o tempo total (~1-2 horas com delay de 1s)
   - Pedir confirmação antes de iniciar
   - Coletar dados página por página
   - Salvar no banco `data/tcrb_observations.db`
   - Mostrar progresso e estatísticas

3. **Exemplo de saída:**

```
======================================================================
COLETOR DE DADOS HISTÓRICOS - T CrB (AAVSO)
======================================================================

✅ Banco de dados inicializado

Descobrindo número total de páginas...
✅ Total de páginas encontradas: 3600
📊 Estimativa de observações: ~720,000

⚠️  ATENÇÃO: Este processo pode levar várias horas!
   Serão feitas 3,600 requisições ao servidor AAVSO
   Com delay de 1s entre requisições

Deseja continuar? (s/N): s

======================================================================
INICIANDO COLETA DE DADOS
======================================================================

Coletando página 1... ✅ 200 observações coletadas
   💾 Salvos: 200 novos | Total coletado: 200 | Progresso: 1/3600 (0.0%)
   ⏱️  Tempo decorrido: 0.5min | Estimativa restante: 30.0min

Coletando página 2... ✅ 200 observações coletadas
   💾 Salvos: 200 novos | Total coletado: 400 | Progresso: 2/3600 (0.1%)
   ⏱️  Tempo decorrido: 1.0min | Estimativa restante: 29.5min

...
```

### Estrutura do Banco de Dados

O script cria automaticamente a tabela `observations` com a seguinte estrutura:

```sql
CREATE TABLE observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    star TEXT NOT NULL,
    date_original TEXT NOT NULL,      -- Data original do AAVSO
    date_br TEXT NOT NULL,             -- Data em formato brasileiro
    magnitude REAL NOT NULL,
    observer TEXT,
    obs_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(star, date_original, magnitude, observer)
);
```

### Consultas Úteis

Após a coleta, você pode consultar os dados:

```sql
-- Total de observações
SELECT COUNT(*) FROM observations;

-- Observações mais recentes
SELECT date_br, magnitude, observer 
FROM observations 
ORDER BY date_original DESC 
LIMIT 10;

-- Estatísticas por ano
SELECT 
    substr(date_br, 7, 4) as ano,
    COUNT(*) as total,
    MIN(magnitude) as mag_min,
    MAX(magnitude) as mag_max,
    AVG(magnitude) as mag_media
FROM observations
GROUP BY ano
ORDER BY ano DESC;

-- Observadores mais ativos
SELECT 
    observer,
    COUNT(*) as total_obs
FROM observations
GROUP BY observer
ORDER BY total_obs DESC
LIMIT 10;
```

### Interrupção e Retomada

- O script pode ser interrompido a qualquer momento (Ctrl+C)
- Ao executar novamente, ele **não irá duplicar dados**
- A cláusula `INSERT OR IGNORE` garante que apenas novos dados sejam inseridos
- Você pode executar o script múltiplas vezes para atualizar os dados

### Tempo Estimado

Com as configurações padrão:
- **Delay entre requisições:** 1 segundo
- **Total de páginas:** ~3600
- **Tempo estimado:** 1-2 horas

Para acelerar (não recomendado):
- Edite `DELAY_BETWEEN_REQUESTS` em [`historical_scraper.py`](historical_scraper.py:15)
- ⚠️ **Cuidado:** Delays muito curtos podem sobrecarregar o servidor AAVSO

### Solução de Problemas

**Erro de conexão:**
```bash
❌ Erro na requisição: Connection timeout
```
- Verifique sua conexão com a internet
- O servidor AAVSO pode estar temporariamente indisponível
- Execute o script novamente mais tarde

**Tabela não encontrada:**
```bash
❌ Tabela não encontrada
```
- A estrutura HTML do AAVSO pode ter mudado
- Verifique se a URL está correta
- Reporte o problema

**Banco de dados bloqueado:**
```bash
⚠️  Erro ao salvar observação: database is locked
```
- Feche outros programas que possam estar acessando o banco
- Execute o script novamente

### Próximos Passos

Após coletar os dados históricos:

1. **Análise de dados:** Use Python/Pandas para análises estatísticas
2. **Visualizações:** Crie gráficos da evolução da magnitude
3. **Exportação:** Exporte para CSV/JSON se necessário
4. **Integração:** Importe para o banco D1 do Cloudflare (se desejar)

### Exemplo de Análise com Pandas

```python
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# Carrega dados
conn = sqlite3.connect('data/tcrb_observations.db')
df = pd.read_sql_query("SELECT * FROM observations", conn)
conn.close()

# Converte data para datetime
df['date'] = pd.to_datetime(df['date_br'], format='%d/%m/%Y %H:%M')

# Plota evolução da magnitude
plt.figure(figsize=(15, 6))
plt.plot(df['date'], df['magnitude'], 'o', markersize=1, alpha=0.5)
plt.xlabel('Data')
plt.ylabel('Magnitude')
plt.title('Evolução da Magnitude de T CrB')
plt.gca().invert_yaxis()  # Inverte eixo Y (magnitudes menores = mais brilhante)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('tcrb_evolution.png', dpi=300)
plt.show()
```

## Notas Importantes

- 📊 O AAVSO contém **centenas de milhares** de observações de T CrB
- ⏱️ A coleta completa pode levar **1-2 horas**
- 💾 O banco de dados final terá **~100-200 MB**
- 🌐 Respeite o servidor AAVSO mantendo o delay entre requisições
- 🔄 Execute periodicamente para manter os dados atualizados

## Suporte

Para problemas ou dúvidas:
1. Verifique os logs de erro do script
2. Consulte a documentação do AAVSO
3. Reporte issues no repositório do projeto