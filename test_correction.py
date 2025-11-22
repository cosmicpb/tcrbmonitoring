#!/usr/bin/env python3
"""
Testa a correção coletando 3 páginas e verificando se tem ~200 obs/página
"""

import sys
sys.path.insert(0, '.')

from robust_scraper import scrape_page, save_batch, init_database
import sqlite3

DB_PATH = "data/tcrb_observations.db"

def test_correction():
    """Testa coleta de 3 páginas"""
    print("=" * 60)
    print("TESTE DE CORREÇÃO")
    print("=" * 60)
    print()
    
    init_database()
    
    # Testa páginas problemáticas identificadas nos logs
    test_pages = [383, 386, 391]
    all_observations = []
    
    for page in test_pages:
        print(f"🔍 Coletando página {page}...")
        result = scrape_page(page)
        
        if result['error']:
            print(f"   ❌ Erro: {result['error']}")
        else:
            obs_count = len(result['observations'])
            all_observations.extend(result['observations'])
            print(f"   ✅ Coletadas: {obs_count} observações")
            
            # Verifica se está no range esperado (190-210)
            if obs_count < 190 or obs_count > 210:
                print(f"   ⚠️  ATENÇÃO: Esperado ~200, obtido {obs_count}")
            else:
                print(f"   ✅ OK: Dentro do esperado (~200)")
    
    print()
    print(f"📊 Total coletado: {len(all_observations)} observações")
    print(f"📊 Média por página: {len(all_observations) / len(test_pages):.1f} obs/página")
    
    # Salva no banco
    print()
    print("💾 Salvando no banco...")
    saved = save_batch(all_observations)
    print(f"✅ Salvas: {saved} observações")
    
    # Verifica no banco
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM observations")
    total_db = cursor.fetchone()[0]
    conn.close()
    
    print(f"✅ Total no banco: {total_db}")
    
    print()
    print("=" * 60)
    
    # Validação final
    avg_per_page = len(all_observations) / len(test_pages)
    if avg_per_page >= 190 and avg_per_page <= 210:
        print("✅ CORREÇÃO VALIDADA! Média de ~200 obs/página")
        print("✅ Pronto para coleta massiva!")
        return True
    else:
        print(f"❌ PROBLEMA: Média de {avg_per_page:.1f} obs/página")
        print("❌ Esperado: ~200 obs/página")
        return False

if __name__ == "__main__":
    success = test_correction()
    sys.exit(0 if success else 1)