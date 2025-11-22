# Análise do Scraper AAVSO - T CrB

## Data: 2025-11-11

## Problema Reportado
Usuário notou que há observações faltando na coleta de 716.745 observações.

## Investigação

### 1. Análise da Estrutura HTML

#### Com num_results=20 (página pequena)
```html
<tr class='obs tr-even' id='ob-0'>
  <!-- Dados da observação -->
</tr>
<tr id='ob-0-detail' class='obs-detail-tr'>
  <!-- Detalhes expandíveis -->
</tr>
```

- **20 observações principais** (`class='obs'`)
- **25 linhas de detalhes** (`class='obs-detail-tr'`)
- **Total: 45 linhas** com class contendo "obs"

#### Com num_results=200 (página grande)
```html
<tr class='obs tr-even' id='ob-0'>
  <!-- Dados da observação -->
</tr>
<!-- SEM linha de detalhes! -->
```

- **200 observações principais** (`class='obs'`)
- **0 linhas de detalhes** (não incluídas pelo AAVSO)
- **Total: 200 linhas** com class contendo "obs"

### 2. Comportamento do AAVSO

O site AAVSO tem comportamento diferente baseado em `num_results`:

| num_results | Observações | Linhas de Detalhes | Total de `<tr class='obs'>` |
|-------------|-------------|--------------------|-----------------------------|
| 20          | 20          | 20-25              | 40-45                       |
| 50          | 50          | 50-60              | 100-110                     |
| 200         | 200         | 0                  | 200                         |

**Conclusão:** Com `num_results=200`, o AAVSO **não inclui** linhas de detalhes expandíveis.

### 3. Validação do Scraper Atual

#### robust_scraper.py (linhas 205-207)
```python
# Pega APENAS linhas principais (class exatamente "obs", não "obs-detail-tr")
all_rows = table.find_all('tr', class_='obs')
rows = [row for row in all_rows if 'obs-detail-tr' not in row.get('class', [])]
```

**Status:** ✅ **CORRETO** - O filtro funciona, mas é desnecessário para `num_results=200`

#### Teste Realizado
```bash
$ python test_improved_scraper.py
Total de linhas: 200
- Linhas principais (obs): 200
- Linhas de detalhes (obs-detail-tr): 0
```

**Resultado:** ✅ **Scraper está coletando corretamente**

## Possíveis Causas de Dados Faltando

Se há observações faltando, as causas podem ser:

### 1. ❌ Linhas de Detalhes (DESCARTADO)
- **Motivo:** Com `num_results=200`, não há linhas de detalhes
- **Status:** Não é o problema

### 2. ⚠️ Páginas Puladas
- **Verificar:** Arquivo `data/checkpoint_improved.txt`
- **Ação:** Conferir se todas as 3.608 páginas foram coletadas

### 3. ⚠️ Erros de Parsing
- **Verificar:** Logs em `logs/scraper_*.log`
- **Ação:** Procurar por linhas com "Erro ao fazer parse"

### 4. ⚠️ Duplicatas Ignoradas
- **Verificar:** Constraint UNIQUE no banco
- **Ação:** Verificar quantas duplicatas foram encontradas

### 5. ⚠️ Timeout/Rate Limiting
- **Verificar:** Logs de HTTP 429, 503, timeouts
- **Ação:** Reprocessar páginas com erro

## Recomendações

### 1. Verificar Checkpoint
```bash
wc -l data/checkpoint_improved.txt
# Deve ter 3608 linhas
```

### 2. Verificar Logs
```bash
grep -i "erro\|warning\|falha" logs/scraper_*.log | wc -l
```

### 3. Comparar Contagens
```sql
-- Total no banco
SELECT COUNT(*) FROM observations;

-- Esperado: 721.892 (segundo AAVSO)
-- Coletado: 716.745
-- Diferença: 5.147 observações
```

### 4. Verificar Duplicatas
```bash
grep "duplicadas" logs/scraper_*.log | tail -20
```

## Próximos Passos

1. ✅ Scraper está correto para `num_results=200`
2. ⏳ Investigar por que 5.147 observações estão faltando
3. ⏳ Verificar se todas as páginas foram processadas
4. ⏳ Analisar logs para erros de parsing
5. ⏳ Considerar reprocessar páginas com erro

## Conclusão

O scraper **NÃO** tem bug de coleta de linhas de detalhes quando usa `num_results=200`. 

As observações faltando (5.147) podem ser devido a:
- Páginas não processadas
- Erros de parsing em páginas específicas
- Duplicatas legítimas
- Mudanças no site durante a coleta

**Ação recomendada:** Analisar logs e checkpoint para identificar a causa real.