#!/usr/bin/env python3
"""
Limpa dados incorretos coletados com o bug das linhas de Details
"""

import sqlite3
from datetime import datetime

DB_PATH = "data/tcrb_observations.db"

def clean_database():
    """Remove dados coletados após o bug ser descoberto"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Conta total antes
    cursor.execute("SELECT COUNT(*) FROM observations")
    total_before = cursor.fetchone()[0]
    print(f"📊 Total de observações ANTES: {total_before:,}")
    
    # Remove dados coletados após 15:38 (quando o bug foi detectado)
    cursor.execute("""
        DELETE FROM observations 
        WHERE created_at >= '2025-11-08 15:38:00'
    """)
    
    deleted = cursor.rowcount
    conn.commit()
    
    # Conta total depois
    cursor.execute("SELECT COUNT(*) FROM observations")
    total_after = cursor.fetchone()[0]
    
    print(f"🗑️  Observações removidas: {deleted:,}")
    print(f"✅ Total de observações DEPOIS: {total_after:,}")
    
    # Mostra estatísticas
    cursor.execute("""
        SELECT 
            MIN(calendar_date) as primeira,
            MAX(calendar_date) as ultima,
            COUNT(DISTINCT observer) as observadores
        FROM observations
    """)
    
    stats = cursor.fetchone()
    if stats[0]:
        print(f"\n📅 Período dos dados restantes:")
        print(f"   Primeira: {stats[0]}")
        print(f"   Última: {stats[1]}")
        print(f"   Observadores: {stats[2]}")
    
    conn.close()
    print("\n✅ Limpeza concluída!")

if __name__ == "__main__":
    print("=" * 60)
    print("LIMPEZA DE DADOS INCORRETOS")
    print("=" * 60)
    print()
    
    confirm = input("Remover dados coletados após 15:38? (s/N): ").strip().lower()
    if confirm == 's':
        clean_database()
    else:
        print("❌ Cancelado")