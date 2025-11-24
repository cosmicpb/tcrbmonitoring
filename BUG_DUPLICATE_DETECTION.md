# 🐛 Bug: Detecção de Duplicatas Incorreta no Scraper

**Data:** 24/11/2025 09:34 BRT
**Versão Afetada:** v2.3
**Versão Corrigida:** v2.4.1
**Severidade:** 🔴 **ALTA** - Perda de dados

---

## 📋 Resumo

O scraper estava **perdendo observações válidas** ao considerar apenas o campo `jd` (Julian Date) para detectar duplicatas. Como múltiplas observações podem ter o **mesmo JD e mesmo Observer** mas **magnitudes diferentes** (medições com filtros diferentes no mesmo momento), o scraper estava rejeitando observações legítimas como duplicatas.

---

## 🔍 Descoberta do Bug

### Observações Reportadas pelo Usuário

O usuário notou que estas 3 observações do AAVSO:

| ID | JD | Magnitude | Filter | Observer | Status |
|----|----|-----------| -------|----------|--------|
| ob-6 | 2461002.24360764 | 11.0255 | **TB** | MCHB | ✅ Coletada |
| ob-7 | 2461002.24360764 | 9.9277 | **TG** | MCHB | ❌ **NÃO coletada** |
| ob-8 | 2461002.24360764 | 9.225 | **TR** | MCHB | ❌ **NÃO coletada** |

**Problema:** Apenas ob-6 foi salva no banco, as outras duas foram rejeitadas como "duplicatas".

### Análise do Código

**Código ANTES (v2.3):**
```python
# Linha 233 - workers/scraper/scraper-worker.py
check_query = "SELECT COUNT(*) as count FROM observations WHERE jd = ?"
result = await env.DB.prepare(check_query).bind(data['jd']).first()
```

**Problema Identificado:**
- ❌ Usa apenas `jd` como chave de unicidade
- ❌ Ignora que múltiplas observações podem ter o mesmo JD e Observer
- ❌ Rejeita observações com magnitudes diferentes como duplicatas

---

## 🎯 Causa Raiz

### Conceito Astronômico

No AAVSO, é **comum e esperado** que múltiplas observações tenham o **mesmo Julian Date e mesmo Observer** quando:

1. **Observações Multi-Filtro:** Mesmo observador faz medições simultâneas com filtros diferentes (TB, TG, TR, etc.), resultando em **magnitudes diferentes**
2. **Múltiplos Instrumentos:** Mesmo observador usa múltiplos instrumentos no mesmo momento
3. **Observadores Diferentes:** Múltiplos observadores fazem medições no mesmo momento (JD igual, observers diferentes)

### Exemplo Real

```
JD: 2461002.24360764 (22/11/2025 05:51 UTC)
├─ TB (Blue Filter)    → Mag: 11.0255 ✅ Salva
├─ TG (Green Filter)   → Mag: 9.9277  ❌ Rejeitada (duplicata!)
└─ TR (Red Filter)     → Mag: 9.225   ❌ Rejeitada (duplicata!)
```

---

## ✅ Solução Implementada

### Código DEPOIS (v2.4.1)

```python
# Linha 232-235 - workers/scraper/scraper-worker.py
# Verifica se já existe (considera JD + Observer + Magnitude como chave única)
# Mesmo observador pode fazer múltiplas medições no mesmo JD com filtros diferentes,
# resultando em magnitudes diferentes. A magnitude é o que diferencia cada observação.
check_query = "SELECT COUNT(*) as count FROM observations WHERE jd = ? AND observer = ? AND magnitude = ?"
result = await env.DB.prepare(check_query).bind(data['jd'], data['observer'], data['magnitude']).first()
```

### Chave de Unicidade

**ANTES:** `jd`
**DEPOIS:** `jd + observer + magnitude`

### Justificativa

A combinação `(jd, observer, magnitude)` garante que:

✅ Observações com mesmo JD e Observer mas magnitudes diferentes são aceitas (filtros diferentes)
✅ Observações com mesmo JD mas observadores diferentes são aceitas
✅ Duplicatas reais (mesmo JD, Observer E Magnitude) são rejeitadas

**Por que Magnitude e não Filter?**
- A magnitude é o **resultado da medição** e identifica unicamente cada observação
- Filtros diferentes produzem magnitudes diferentes
- É mais robusto que usar o filtro, pois captura a essência da observação

---

## 📊 Impacto

### Dados Perdidos

Estimativa de observações perdidas desde o deploy v2.3 (22/11/2025):

- **Período:** 22/11/2025 15:39 até 24/11/2025 09:34 (~42 horas)
- **Execuções do cron:** ~42 execuções
- **Observações multi-filtro típicas:** ~2-5 por execução
- **Estimativa de perda:** **84-210 observações**

### Observações Afetadas

Todas as observações que tinham:
- Mesmo JD de uma observação já coletada
- Filtro diferente
- Mesmo ou diferente observador

---

## 🔧 Correção Aplicada

### Deploy v2.4.1

```
Worker Name:     tcrb-scraper
Version ID:      405e1840-d3cc-4346-bfc8-ccf532e21c38
Deploy Time:     24/11/2025 09:38 BRT
Bundle Size:     12.45 KiB (gzip: 3.59 KiB)
Startup Time:    890 ms
Status:          ✅ DEPLOYED
```

### Mudanças

1. **Detecção de Duplicatas:** Agora usa `(jd, observer, magnitude)` como chave única
2. **Comentários:** Adicionados para explicar a lógica e justificar uso de magnitude
3. **Logs:** Mantidos para debugging

---

## 🧪 Validação

### Teste Manual

Para validar a correção, aguardar a próxima execução do cron e verificar:

1. ✅ Observações com mesmo JD e Observer mas magnitudes diferentes são coletadas
2. ✅ Duplicatas reais (mesmo JD, Observer e Magnitude) são rejeitadas
3. ✅ Logs mostram corretamente "Nova observação" vs "Duplicada"

### Exemplo Esperado

```
[SCRAPER] Página 1: 20 observações
[SCRAPER] ✅ Nova observação salva (JD: 2461002.24360764, Filter: TB)
[SCRAPER] ✅ Nova observação salva (JD: 2461002.24360764, Filter: TG)
[SCRAPER] ✅ Nova observação salva (JD: 2461002.24360764, Filter: TR)
[SCRAPER] Resumo: 3 novas, 0 duplicadas
```

---

## 📈 Recuperação de Dados

### Opção 1: Aguardar Coleta Natural

As observações perdidas eventualmente serão coletadas quando:
- O scraper coletar páginas mais antigas (15 páginas = 300 obs)
- As observações ainda estiverem nas primeiras 15 páginas

**Vantagem:** Automático, sem intervenção  
**Desvantagem:** Pode demorar se houver muitas observações novas

### Opção 2: Coleta Manual Retroativa

Executar script para coletar páginas específicas do período afetado:

```python
# Coletar páginas 1-20 para recuperar dados perdidos
for page in range(1, 21):
    observations = await scrape_page(page)
    for obs in observations:
        await save_to_d1(env, obs)
```

**Vantagem:** Recuperação imediata  
**Desvantagem:** Requer execução manual

---

## 🎓 Lições Aprendidas

### 1. Validar Suposições de Unicidade

❌ **Erro:** Assumir que JD é único
✅ **Correto:** Validar com dados reais do AAVSO e entender o domínio

### 2. Testar com Dados Multi-Filtro

❌ **Erro:** Testar apenas com observações single-filter
✅ **Correto:** Incluir casos de observações simultâneas com filtros diferentes

### 3. Documentar Lógica de Negócio

❌ **Erro:** Código sem comentários sobre unicidade
✅ **Correto:** Comentários explicando por que `(jd, observer, magnitude)` é a chave

### 4. Escolher Chave Natural

❌ **Erro:** Usar campos técnicos (filter) como chave
✅ **Correto:** Usar o resultado da medição (magnitude) que identifica a observação

### 4. Monitorar Logs de Duplicatas

❌ **Erro:** Não analisar taxa de duplicatas  
✅ **Correto:** Taxa anormalmente alta de duplicatas indica bug

---

## 📝 Recomendações

### Curto Prazo

1. ✅ **Monitorar próxima execução do cron** para validar correção
2. ⏳ **Verificar logs** para confirmar que observações multi-filtro são aceitas
3. ⏳ **Comparar contagem** de observações antes/depois

### Médio Prazo

1. ⏳ **Criar índice composto** no D1: `CREATE INDEX idx_unique_obs ON observations(jd, observer, magnitude)`
2. ⏳ **Adicionar constraint UNIQUE** no schema para prevenir duplicatas no banco
3. ⏳ **Implementar testes automatizados** para casos multi-filtro

### Longo Prazo

1. ⏳ **Dashboard de monitoramento** com métricas de coleta
2. ⏳ **Alertas automáticos** para taxa anormal de duplicatas
3. ⏳ **Validação de dados** comparando com API do AAVSO

---

## 🔗 Referências

- **Código Afetado:** [`workers/scraper/scraper-worker.py:233`](workers/scraper/scraper-worker.py#L233)
- **Deploy v2.3:** [`DEPLOY_SCRAPER_V2.3.md`](DEPLOY_SCRAPER_V2.3.md)
- **AAVSO Data Format:** https://www.aavso.org/aavso-international-database

---

## 📊 Status

| Item | Status |
|------|--------|
| **Bug Identificado** | ✅ Completo |
| **Causa Raiz Analisada** | ✅ Completo |
| **Correção Implementada** | ✅ Completo |
| **Deploy Realizado** | ✅ Completo |
| **Validação** | ⏳ Aguardando próxima execução |
| **Recuperação de Dados** | ⏳ Pendente |
| **Documentação** | ✅ Completo |

---

**Relatório criado por:** Kilo Code  
**Data:** 24/11/2025 09:34 BRT  
**Versão:** 1.0