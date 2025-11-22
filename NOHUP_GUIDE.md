# Guia de Execução com Nohup

## Executar o Scraper em Background

### Opção 1: Usando o script wrapper (RECOMENDADO)

```bash
./run_scraper_nohup.sh
```

Este script:
- ✅ Inicia o scraper em background
- ✅ Auto-responde 's' para confirmações
- ✅ Salva o PID em `scraper.pid`
- ✅ Redireciona output para `nohup.out`

### Opção 2: Comando direto

```bash
nohup python3 -u run_scraper.py > nohup.out 2>&1 &
```

**Importante:** O `-u` força output unbuffered (logs em tempo real)

## Monitorar o Progresso

### Ver logs em tempo real:

```bash
# Output geral (nohup.out)
tail -f nohup.out

# Logs detalhados do scraper
tail -f logs/scraper_*.log

# Último arquivo de log
tail -f $(ls -t logs/scraper_*.log | head -1)
```

### Ver progresso resumido:

```bash
# Últimas 20 linhas
tail -20 nohup.out

# Buscar por checkpoints
grep "Checkpoint salvo" logs/scraper_*.log | tail -10

# Contar observações salvas
sqlite3 data/tcrb_observations.db "SELECT COUNT(*) FROM observations;"
```

## Parar o Scraper

### Opção 1: Usando o PID salvo

```bash
kill $(cat scraper.pid)
```

### Opção 2: Encontrar e matar o processo

```bash
# Encontrar o PID
ps aux | grep robust_scraper.py

# Matar o processo (substitua PID pelo número encontrado)
kill PID
```

### Opção 3: Parar todos os scrapers

```bash
pkill -f robust_scraper.py
```

## Verificar Status

### Verificar se está rodando:

```bash
# Verificar processo
ps aux | grep robust_scraper.py

# Verificar PID salvo
if [ -f scraper.pid ]; then
    PID=$(cat scraper.pid)
    if ps -p $PID > /dev/null; then
        echo "✅ Scraper rodando (PID: $PID)"
    else
        echo "❌ Scraper não está rodando"
    fi
else
    echo "⚠️  Arquivo scraper.pid não encontrado"
fi
```

### Verificar progresso no banco:

```bash
# Total de observações
sqlite3 data/tcrb_observations.db "SELECT COUNT(*) FROM observations;"

# Observações por data
sqlite3 data/tcrb_observations.db "
SELECT 
    DATE(created_at) as data,
    COUNT(*) as total
FROM observations 
GROUP BY DATE(created_at)
ORDER BY data DESC;"

# Últimas observações coletadas
sqlite3 data/tcrb_observations.db "
SELECT 
    calendar_date,
    magnitude,
    observer
FROM observations 
ORDER BY created_at DESC 
LIMIT 10;"
```

## Retomar Após Interrupção

O scraper tem checkpoint automático. Se for interrompido:

1. **Verificar checkpoint:**
   ```bash
   cat data/scraper_checkpoint.json
   ```

2. **Reiniciar:**
   ```bash
   ./run_scraper_nohup.sh
   ```

3. **Responder 's' quando perguntar se quer retomar**

## Arquivos Importantes

| Arquivo | Descrição |
|---------|-----------|
| `nohup.out` | Output geral do scraper |
| `logs/scraper_*.log` | Logs detalhados com timestamp |
| `data/scraper_checkpoint.json` | Checkpoint (páginas completadas) |
| `data/failed_pages.json` | Páginas que falharam |
| `scraper.pid` | PID do processo em execução |
| `data/tcrb_observations.db` | Banco de dados SQLite |

## Troubleshooting

### Scraper não inicia:

```bash
# Verificar dependências
pip3 install -r requirements.txt

# Verificar permissões
chmod +x run_scraper_nohup.sh
chmod +x run_scraper.py
```

### Logs não aparecem em tempo real:

```bash
# Use -u para unbuffered output
nohup python3 -u run_scraper.py > nohup.out 2>&1 &
```

### Múltiplas instâncias rodando:

```bash
# Matar todas
pkill -f robust_scraper.py

# Limpar PID
rm -f scraper.pid

# Reiniciar
./run_scraper_nohup.sh
```

## Estimativas

- **Total de páginas:** 3.608
- **Observações por página:** ~200
- **Total esperado:** ~721.600 observações
- **Tempo estimado:** ~2-3 horas (com 16 workers)
- **Velocidade:** ~20-30 páginas/minuto

## Após Conclusão

1. Verificar total de observações:
   ```bash
   sqlite3 data/tcrb_observations.db "SELECT COUNT(*) FROM observations;"
   ```

2. Verificar páginas com falha:
   ```bash
   cat data/failed_pages.json
   ```

3. Migrar para D1:
   ```bash
   python3 migrate_to_d1.py