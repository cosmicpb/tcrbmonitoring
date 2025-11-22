#!/usr/bin/env python3
"""
Script para sincronizar dados do SQLite local para o D1 da Cloudflare
Migra apenas observações que não existem no D1
"""

import sqlite3
import requests
import time
from datetime import datetime

# Configurações
LOCAL_DB = "data/tcrb_observations.db"
D1_API_URL = "https://tcrb-api.pbaldacimjr.workers.dev"
BATCH_SIZE = 100  # Número de observações por batch

def get_local_observations():
    """Busca todas as observações do SQLite local"""
    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT star, jd, calendar_date, magnitude, error, band, observer
        FROM observations
        ORDER BY jd DESC
    """)
    
    observations = cursor.fetchall()
    conn.close()
    
    return observations

def get_d1_jds():
    """Busca todos os JDs que já existem no D1"""
    print("🔍 Buscando JDs existentes no D1...")
    jds = set()
    page = 1
    
    while True:
        try:
            response = requests.get(f"{D1_API_URL}/observations?page={page}&limit=1000")
            data = response.json()
            
            if data['status'] != 'success':
                break
            
            for obs in data['observations']:
                jds.add(obs['jd'])
            
            print(f"   Página {page}: {len(data['observations'])} observações")
            
            if not data['pagination']['has_next']:
                break
            
            page += 1
            time.sleep(0.1)  # Rate limiting
            
        except Exception as e:
            print(f"❌ Erro ao buscar página {page}: {e}")
            break
    
    print(f"✅ Total de JDs no D1: {len(jds)}")
    return jds

def main():
    print("=" * 80)
    print("SINCRONIZAÇÃO SQLite → D1")
    print("=" * 80)
    print()
    
    # 1. Busca dados locais
    print("📊 Buscando observações locais...")
    local_obs = get_local_observations()
    print(f"✅ Total local: {len(local_obs):,} observações")
    print()
    
    # 2. Busca JDs existentes no D1
    d1_jds = get_d1_jds()
    print()
    
    # 3. Identifica observações faltantes
    print("🔍 Identificando observações faltantes...")
    missing = []
    
    for obs in local_obs:
        star, jd, calendar_date, magnitude, error, band, observer = obs
        
        # Verifica se JD não existe no D1
        if jd not in d1_jds:
            missing.append({
                'star': star,
                'jd': jd,
                'calendar_date': calendar_date,
                'magnitude': magnitude,
                'error': error if error else '&mdash;',
                'band': band if band else '&mdash;',
                'observer': observer
            })
    
    print(f"✅ Observações faltantes: {len(missing):,}")
    print()
    
    if len(missing) == 0:
        print("✅ Todos os dados já estão sincronizados!")
        return
    
    # 4. Mostra amostra
    print("📋 Amostra das observações faltantes:")
    for i, obs in enumerate(missing[:5]):
        print(f"   {i+1}. JD {obs['jd']} - {obs['calendar_date']} - Mag {obs['magnitude']} - {obs['observer']}")
    if len(missing) > 5:
        print(f"   ... e mais {len(missing) - 5} observações")
    print()
    
    # 5. Confirma migração
    confirm = input(f"Migrar {len(missing):,} observações para o D1? (s/N): ").strip().lower()
    if confirm != 's':
        print("❌ Cancelado")
        return
    
    print()
    print("=" * 80)
    print("INICIANDO MIGRAÇÃO")
    print("=" * 80)
    print()
    print("⚠️  NOTA: Esta é uma operação de LEITURA do D1 e ANÁLISE.")
    print("   Para INSERIR dados no D1, você precisará:")
    print("   1. Usar Wrangler CLI com acesso ao D1")
    print("   2. Ou criar um endpoint na API para inserção em batch")
    print()
    print("📝 Salvando lista de observações faltantes em 'missing_observations.json'...")
    
    import json
    with open('missing_observations.json', 'w') as f:
        json.dump(missing, f, indent=2)
    
    print(f"✅ Lista salva com {len(missing):,} observações")
    print()
    print("Para migrar, você pode:")
    print("1. Usar o script migrate_to_d1.py (requer wrangler)")
    print("2. Criar endpoint POST na API para inserção em batch")
    print()

if __name__ == "__main__":
    main()