# 🚀 Migração de Dados Históricos - Pronto para Execução

## Status Atual

✅ **SQLite Local**: 717.132 observações completas  
✅ **D1 (Cloudflare)**: 59 observações (teste bem-sucedido)  
✅ **Scripts**: Corrigidos e testados  
✅ **Scraper Cloudflare**: Corrigido e ativo (coleta a cada hora)

---

## 📋 Pré-requisitos Verificados

- [x] Python 3 instalado
- [x] Node.js v20 configurado (via nvm)
- [x] Wrangler CLI instalado
- [x] Banco SQLite local: `tcrb_observations.db` (717.132 registros)
- [x] Script de migração: `migrate_to_d1.py` (corrigido e testado)
- [x] Scripts de automação: `run_migration.sh` e `check_migration.sh` (executáveis)

---

## 🎯 Execução da Migração Completa

### 1. Iniciar Migração em Background

```bash
./run_migration.sh
```

**O que acontece:**
- Verifica todos os pré-requisitos
- Ativa ambiente virtual Python
- Configura Node.js v20
- Executa migração em background com `nohup` e flag `--yes`
- Salva log em `migration.log`
- Salva PID em `migration.pid`

**Nota:** O script usa a flag `--yes` para pular a confirmação interativa, permitindo execução em background sem intervenção.

**Estimativas:**
- **Total de registros**: 717.132 observações
- **Lotes**: 7.172 lotes (100 registros cada)
- **Tempo estimado**: ~4-5 horas
- **Taxa**: ~40-50 registros/segundo

---

### 2. Monitorar Progresso

#### Opção A: Status Geral (Recomendado)
```bash
./check_migration.sh
```

**Mostra:**
- Status do processo (rodando/parado)
- Últimas 20 linhas do log
- Estatísticas (lotes OK/erro, progresso %)
- Total atual no D1 (via API)
- Comandos úteis

#### Opção B: Tempo Real
```bash
tail -f migration.log
```

**Mostra:**
- Log em tempo real
- Cada lote processado
- Erros (se houver)
- Progresso detalhado

#### Opção C: Estatísticas Rápidas
```bash
# Total de lotes processados
grep "Batch" migration.log | wc -l

# Lotes com sucesso
grep "successfully" migration.log | wc -l

# Erros
grep "Error" migration.log | wc -l

# Último lote processado
grep "Batch" migration.log | tail -1
```

---

### 3. Verificar Conclusão

Quando a migração terminar, você verá no log:

```
✅ Migration completed successfully!
Total batches: 7172
Total records migrated: 717132
```

**Verificar total no D1:**
```bash
curl https://tcrb-api.baldacim.workers.dev/api/observations/count
```

Deve retornar aproximadamente:
```json
{"count": 717191}
```
(59 existentes + 717.132 migrados = 717.191 total)

---

## 🛠️ Comandos Úteis Durante a Migração

### Parar a Migração (se necessário)
```bash
# Obter PID
cat migration.pid

# Parar processo
kill $(cat migration.pid)

# Ou forçar
kill -9 $(cat migration.pid)
```

### Reiniciar do Ponto de Parada
O script detecta automaticamente onde parou e continua de lá:
```bash
./run_migration.sh
```

### Executar Manualmente (com confirmação)
Se preferir executar manualmente com confirmação interativa:
```bash
source venv/bin/activate
python3 migrate_to_d1.py
```

### Executar Manualmente (sem confirmação)
Para executar em foreground sem confirmação:
```bash
source venv/bin/activate
python3 migrate_to_d1.py --yes
```

### Limpar e Recomeçar do Zero
```bash
# Parar processo
kill $(cat migration.pid)

# Limpar arquivos
rm migration.log migration.pid

# Recomeçar
./run_migration.sh
```

---

## 📊 Estrutura dos Dados Migrados

### Schema D1 (Correto)
```sql
CREATE TABLE observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    star TEXT NOT NULL,
    jd TEXT NOT NULL,              -- Julian Date
    calendar_date TEXT NOT NULL,   -- Data formatada
    magnitude TEXT NOT NULL,       -- Magnitude visual
    error TEXT,                    -- Erro da medição
    filter TEXT,                   -- Filtro usado
    observer TEXT,                 -- Código do observador
    scraped_at TEXT,               -- Timestamp da coleta
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(star, jd, magnitude, filter, observer)
);
```

### Mapeamento SQLite → D1
- `date_original` → `jd`
- `date_br` → `calendar_date`
- `band` → `filter`
- `created_at` → `scraped_at`
- `magnitude` (REAL) → `magnitude` (TEXT)
- `error` (REAL) → `error` (TEXT)

---

## ⚠️ Pontos de Atenção

### 1. Duplicatas
- O script usa `INSERT OR IGNORE` para evitar duplicatas
- Chave única: `(star, jd, magnitude, filter, observer)`
- Registros duplicados são silenciosamente ignorados

### 2. Rate Limiting
- Cloudflare D1 tem limites de taxa
- O script usa batches de 100 registros
- Delay de 0.5s entre batches para evitar throttling

### 3. Erros Temporários
- Erros de rede são esperados ocasionalmente
- O script continua automaticamente após erros
- Verifique `migration.log` para detalhes

### 4. Espaço em Disco
- D1 Free Tier: 5 GB de armazenamento
- Estimativa: ~717k registros ≈ 100-150 MB
- Bem dentro do limite

---

## 🎉 Após a Migração

### 1. Validar Dados
```bash
# Total de registros
curl https://tcrb-api.baldacim.workers.dev/api/observations/count

# Últimas observações
curl https://tcrb-api.baldacim.workers.dev/api/observations?limit=10

# Observações de um período específico
curl "https://tcrb-api.baldacim.workers.dev/api/observations?start_date=2024-01-01&end_date=2024-12-31"
```

### 2. Atualizar Documentação
- Atualizar README.md com novo total de dados
- Documentar processo de migração
- Adicionar estatísticas finais

### 3. Monitoramento Contínuo
- Scraper Cloudflare coleta novos dados a cada hora
- API serve dados históricos + novos dados
- Verificar logs periodicamente: `npx wrangler tail`

---

## 📝 Logs e Arquivos Gerados

```
migration.log       # Log completo da migração
migration.pid       # PID do processo em execução
nohup.out          # Output do nohup (backup)
```

---

## 🆘 Troubleshooting

### Problema: "Migration already running"
**Solução:**
```bash
# Verificar se realmente está rodando
ps aux | grep migrate_to_d1.py

# Se não estiver, remover PID antigo
rm migration.pid

# Tentar novamente
./run_migration.sh
```

### Problema: "wrangler: command not found"
**Solução:**
```bash
# Instalar wrangler
npm install -g wrangler

# Ou usar npx
npx wrangler --version
```

### Problema: Migração muito lenta
**Solução:**
```bash
# Aumentar batch size (editar migrate_to_d1.py)
BATCH_SIZE = 200  # Padrão: 100

# Reduzir delay (editar migrate_to_d1.py)
time.sleep(0.2)  # Padrão: 0.5
```

### Problema: Muitos erros no log
**Solução:**
```bash
# Verificar conectividade
curl https://tcrb-api.baldacim.workers.dev/health

# Verificar autenticação wrangler
npx wrangler whoami

# Re-autenticar se necessário
npx wrangler login
```

---

## 📞 Suporte

Se encontrar problemas:

1. Verificar `migration.log` para detalhes do erro
2. Executar `./check_migration.sh` para diagnóstico
3. Consultar documentação do Cloudflare D1
4. Verificar status do Cloudflare: https://www.cloudflarestatus.com/

---

## ✅ Checklist Final

Antes de executar:
- [ ] Backup do banco SQLite local feito
- [ ] Wrangler autenticado (`npx wrangler whoami`)
- [ ] Node.js v20 ativo (`node --version`)
- [ ] Python 3 disponível (`python3 --version`)
- [ ] Espaço em disco suficiente
- [ ] Conexão estável com internet

Durante a execução:
- [ ] Migração iniciada com `./run_migration.sh`
- [ ] Monitoramento ativo com `./check_migration.sh`
- [ ] Log sendo gerado em `migration.log`

Após conclusão:
- [ ] Total no D1 verificado via API
- [ ] Qualidade dos dados validada
- [ ] Documentação atualizada
- [ ] Arquivos temporários limpos (opcional)

---

**Última atualização**: 2025-11-12  
**Status**: ✅ Pronto para execução