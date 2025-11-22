# Arquitetura do Sistema de Alertas T CrB

## 🎯 Objetivo

Criar um sistema que monitore a estrela T CrB e envie alertas via WhatsApp quando houver **5 medições consecutivas abaixo de magnitude 5**, indicando possível erupção iminente.

---

## 🏗️ Arquitetura Completa

### **Visão Geral dos Componentes**

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA COMPLETO                          │
└─────────────────────────────────────────────────────────────┘

1. SCRAPER WORKER (já existe)
   ├─ Coleta dados a cada hora do AAVSO
   └─ Salva em D1: observations

2. ALERT WORKER (novo) ⭐
   ├─ Cron: a cada 15 minutos
   ├─ Verifica condição: 5 medições < 5 mag
   ├─ Consulta subscribers ativos
   └─ Envia WhatsApp via Twilio

3. SUBSCRIPTION API (novo) ⭐
   ├─ POST /subscribe - Cadastrar número
   ├─ POST /unsubscribe - Remover inscrição
   ├─ GET /verify/:token - Confirmar número
   └─ Salva em D1: subscribers

4. LANDING PAGE (novo) ⭐
   ├─ Formulário de inscrição
   ├─ Validação de número WhatsApp
   └─ Confirmação via código
```

---

## 💾 Banco de Dados D1 - Novas Tabelas

### **Schema Completo**

```sql
-- ============================================
-- TABELA DE INSCRITOS
-- ============================================
CREATE TABLE IF NOT EXISTS subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT NOT NULL UNIQUE,              -- Número completo: +5511999999999
    country_code TEXT DEFAULT '+55',         -- Código do país
    verified BOOLEAN DEFAULT 0,              -- Número verificado?
    verification_token TEXT,                 -- Token de verificação (6 dígitos)
    verification_expires TIMESTAMP,          -- Expiração do token (15 min)
    active BOOLEAN DEFAULT 1,                -- Inscrição ativa?
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP,                   -- Quando foi verificado
    last_alert_sent TIMESTAMP,               -- Último alerta enviado
    alert_count INTEGER DEFAULT 0            -- Total de alertas recebidos
);

-- ============================================
-- TABELA DE ALERTAS ENVIADOS (HISTÓRICO)
-- ============================================
CREATE TABLE IF NOT EXISTS alerts_sent (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscriber_id INTEGER NOT NULL,
    trigger_magnitude REAL,                  -- Magnitude que disparou
    observations_count INTEGER,              -- Quantas obs < 5
    message TEXT,                            -- Mensagem enviada
    status TEXT,                             -- 'sent', 'failed', 'pending'
    twilio_sid TEXT,                         -- ID da mensagem Twilio
    error_message TEXT,                      -- Erro se falhou
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
);

-- ============================================
-- TABELA DE ESTADO DO ALERTA (SINGLETON)
-- ============================================
CREATE TABLE IF NOT EXISTS alert_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),   -- Apenas 1 registro
    alert_active BOOLEAN DEFAULT 0,          -- Alerta está ativo?
    alert_triggered_at TIMESTAMP,            -- Quando foi disparado
    observations_snapshot TEXT,              -- JSON das 5 observações
    total_alerts_sent INTEGER DEFAULT 0,     -- Total enviado neste ciclo
    last_check TIMESTAMP                     -- Última verificação
);

-- Inicializa o estado
INSERT OR IGNORE INTO alert_state (id, alert_active) VALUES (1, 0);

-- ============================================
-- ÍNDICES PARA PERFORMANCE
-- ============================================
CREATE INDEX IF NOT EXISTS idx_phone ON subscribers(phone);
CREATE INDEX IF NOT EXISTS idx_active_verified ON subscribers(active, verified);
CREATE INDEX IF NOT EXISTS idx_last_alert ON subscribers(last_alert_sent);
CREATE INDEX IF NOT EXISTS idx_alert_status ON alerts_sent(status, sent_at);
CREATE INDEX IF NOT EXISTS idx_subscriber_alerts ON alerts_sent(subscriber_id, sent_at);
```

---

## 🔄 Fluxo Completo do Sistema

### **1. Inscrição do Usuário**

```
┌──────────────────────────────────────────────────────────┐
│ USUÁRIO ACESSA LANDING PAGE                              │
│ https://tcrb-alerts.pbaldacimjr.workers.dev             │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│ PREENCHE FORMULÁRIO                                       │
│ ├─ País: Brasil (+55)                                    │
│ ├─ DDD: 11                                               │
│ └─ Número: 99999-9999                                    │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│ SUBSCRIPTION API - POST /subscribe                        │
│ ├─ Valida formato: +5511999999999                       │
│ ├─ Gera token: 123456 (6 dígitos)                       │
│ ├─ Expira em: 15 minutos                                │
│ ├─ Salva em D1 (verified=false)                         │
│ └─ Envia código via WhatsApp (Twilio)                   │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│ USUÁRIO RECEBE WHATSAPP                                  │
│ "Seu código de verificação T CrB: 123456"               │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│ USUÁRIO INSERE CÓDIGO NA PÁGINA                          │
│ └─> POST /verify com token                              │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│ API VALIDA E ATIVA                                       │
│ ├─ Verifica token e expiração                           │
│ ├─ Atualiza: verified=true, verified_at=NOW()           │
│ └─> Usuário inscrito com sucesso! ✅                     │
└──────────────────────────────────────────────────────────┘
```

### **2. Monitoramento e Alerta**

```
┌──────────────────────────────────────────────────────────┐
│ SCRAPER WORKER (Cron: 0 * * * *)                        │
│ ├─ Executa a cada hora                                  │
│ ├─ Coleta nova observação do AAVSO                      │
│ └─ Salva em observations                                │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│ ALERT WORKER (Cron: */15 * * * *)                       │
│ ├─ Executa a cada 15 minutos                            │
│ └─> Verifica condição de alerta                         │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│ LÓGICA DE DETECÇÃO                                       │
│                                                          │
│ 1. Consulta últimas 5 observações:                      │
│    SELECT magnitude, date_br                            │
│    FROM observations                                     │
│    WHERE star = 'T CrB'                                 │
│    ORDER BY date_original DESC                          │
│    LIMIT 5                                              │
│                                                          │
│ 2. Verifica se TODAS < 5.0:                            │
│    all(float(obs.magnitude) < 5.0)                      │
│                                                          │
│ 3. Checa estado do alerta:                             │
│    - Se já ativo: não envia novamente                   │
│    - Se inativo: dispara alerta                         │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│ CONDIÇÃO ATENDIDA! (5 obs < 5 mag)                      │
│                                                          │
│ 1. Atualiza alert_state:                                │
│    - alert_active = true                                │
│    - alert_triggered_at = NOW()                         │
│    - observations_snapshot = JSON das 5 obs             │
│                                                          │
│ 2. Busca subscribers ativos:                            │
│    SELECT * FROM subscribers                            │
│    WHERE active = 1 AND verified = 1                    │
│                                                          │
│ 3. Para cada subscriber:                                │
│    ├─ Monta mensagem personalizada                      │
│    ├─ Envia via Twilio WhatsApp API                     │
│    ├─ Registra em alerts_sent                           │
│    ├─ Atualiza last_alert_sent                          │
│    └─ Incrementa alert_count                            │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│ USUÁRIO RECEBE ALERTA NO WHATSAPP                        │
│                                                          │
│ 🚨 ALERTA T CrB - POSSÍVEL ERUPÇÃO! 🚨                  │
│                                                          │
│ As últimas 5 medições estão abaixo de magnitude 5:      │
│                                                          │
│ 📊 Medições recentes:                                    │
│ • 26/10/2025 02:35 - Mag: 4.8                           │
│ • 26/10/2025 01:20 - Mag: 4.6                           │
│ • 25/10/2025 23:45 - Mag: 4.9                           │
│ • 25/10/2025 22:10 - Mag: 4.7                           │
│ • 25/10/2025 20:30 - Mag: 4.5                           │
│                                                          │
│ ⚠️ A estrela pode estar próxima da erupção!             │
│                                                          │
│ 🔗 Mais info:                                            │
│ https://tcrb-api.pbaldacimjr.workers.dev/latest         │
│                                                          │
│ Para cancelar alertas, acesse:                           │
│ https://tcrb-alerts.pbaldacimjr.workers.dev/unsubscribe │
└──────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementação dos Workers

### **1. Alert Worker (alert-worker.py)**

```python
"""
Cloudflare Worker - Alert System T CrB
Monitora observações e envia alertas via WhatsApp
"""

import json
from js import Response, Headers
from twilio.rest import Client

async def check_alert_condition(db):
    """
    Verifica se há 5 medições consecutivas abaixo de magnitude 5
    """
    query = """
        SELECT magnitude, date_br, date_original
        FROM observations 
        WHERE star = 'T CrB'
        ORDER BY date_original DESC 
        LIMIT 5
    """
    
    result = await db.prepare(query).all()
    
    if not result or not hasattr(result, 'results'):
        return False, None
    
    observations = result.results
    
    # Precisa ter pelo menos 5 observações
    if len(observations) < 5:
        print(f"[ALERT] Apenas {len(observations)} observações disponíveis")
        return False, None
    
    # Verifica se todas as 5 últimas são < 5.0
    below_threshold = []
    for obs in observations:
        try:
            mag = float(obs.magnitude)
            if mag < 5.0:
                below_threshold.append({
                    'magnitude': mag,
                    'date': obs.date_br,
                    'date_original': obs.date_original
                })
        except (ValueError, AttributeError):
            continue
    
    # Todas as 5 devem estar abaixo de 5
    if len(below_threshold) >= 5:
        print(f"[ALERT] ⚠️ CONDIÇÃO ATENDIDA! {len(below_threshold)} observações < 5.0")
        return True, below_threshold[:5]
    
    print(f"[ALERT] Condição não atendida: {len(below_threshold)}/5 observações < 5.0")
    return False, None


async def get_alert_state(db):
    """Obtém o estado atual do alerta"""
    query = "SELECT * FROM alert_state WHERE id = 1"
    result = await db.prepare(query).first()
    return result


async def update_alert_state(db, active, observations=None):
    """Atualiza o estado do alerta"""
    if active:
        obs_json = json.dumps(observations) if observations else None
        query = """
            UPDATE alert_state 
            SET alert_active = 1,
                alert_triggered_at = CURRENT_TIMESTAMP,
                observations_snapshot = ?,
                last_check = CURRENT_TIMESTAMP
            WHERE id = 1
        """
        await db.prepare(query).bind(obs_json).run()
    else:
        query = """
            UPDATE alert_state 
            SET last_check = CURRENT_TIMESTAMP
            WHERE id = 1
        """
        await db.prepare(query).run()


async def get_active_subscribers(db):
    """Busca todos os inscritos ativos e verificados"""
    query = """
        SELECT id, phone, alert_count
        FROM subscribers 
        WHERE active = 1 AND verified = 1
    """
    result = await db.prepare(query).all()
    
    if result and hasattr(result, 'results'):
        return result.results
    return []


async def send_whatsapp_alert(phone, observations, twilio_sid, twilio_token):
    """Envia alerta via Twilio WhatsApp"""
    try:
        client = Client(twilio_sid, twilio_token)
        
        # Monta mensagem
        message_body = "🚨 ALERTA T CrB - POSSÍVEL ERUPÇÃO! 🚨\n\n"
        message_body += "As últimas 5 medições estão abaixo de magnitude 5:\n\n"
        message_body += "📊 Medições recentes:\n"
        
        for obs in observations:
            message_body += f"• {obs