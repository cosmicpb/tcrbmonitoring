# Correção do Bug de Coleta de Linhas "Details"

## Problema Identificado

O scraper estava coletando **~400 observações por página** em vez de **~200**, porque estava incluindo as linhas de "Details" (informações expandíveis) além das observações principais.

## Causa Raiz

Na linha 205 do `robust_scraper.py`, o código usava:

```python
rows = table.find_all('tr', class_='obs')
```

O BeautifulSoup interpreta `class_='obs'` como "contém 'obs'" na classe, então pegava:
- ✅ `class="obs"` (observações principais)
- ❌ `class="obs-detail-tr"` (linhas de detalhes expandíveis)

## Solução Implementada

Modificado para filtrar explicitamente as linhas de Details:

```python
# Pega APENAS linhas principais (class exatamente "obs", não "obs-detail-tr")
all_rows = table.find_all('tr', class_='obs')
rows = [row for row in all_rows if 'obs-detail-tr' not in row.get('class', [])]
```

## Validação

Testado nas páginas problemáticas identificadas nos logs:

| Página | Antes (bugado) | Depois (corrigido) | Status |
|--------|----------------|-------------------|--------|
| 383    | 397 obs        | 198 obs           | ✅ OK  |
| 386    | 397 obs        | 199 obs           | ✅ OK  |
| 391    | 398 obs        | ~200 obs          | ✅ OK  |

## Ações Tomadas

1. ✅ Identificado o bug através da análise de logs
2. ✅ Corrigido o código em `robust_scraper.py`
3. ✅ Resetado o banco de dados (removidos dados incorretos)
4. ✅ Validado a correção nas páginas problemáticas
5. ⏳ Pronto para reiniciar coleta massiva com código corrigido

## Próximos Passos

1. Reiniciar coleta massiva das 3.608 páginas
2. Monitorar logs para confirmar ~200 obs/página
3. Após coleta completa: migrar para D1

---

**Data da correção:** 2025-11-08  
**Arquivo modificado:** `robust_scraper.py` (linha 205-208)