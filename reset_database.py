#!/usr/bin/env python3
"""
Reseta o banco de dados completamente
"""

import sqlite3
from pathlib import Path

DB_PATH = "data/tcrb_observations.db"

def reset_database():
    """Remove todos os dados e recria as tabelas"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Conta total antes
    cursor.execute("SELECT COUNT(*) FROM observations")
    total_before = cursor.fetchone()[0]
    print(f"📊 Total de observações: {total_before:,}")
    
    # Remove TODOS os dados
    cursor.execute("DELETE FROM observations")
    deleted = cursor.rowcount
    conn.commit()
    
    # Reseta o autoincrement
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='observations'")
    conn.commit()
    
    # Verifica
    cursor.execute("SELECT COUNT(*) FROM observations")
    total_after = cursor.fetchone()[0]
    
    print(f"🗑️  Observações removidas: {deleted:,}")
    print(f"✅ Total após limpeza: {total_after}")
    
    conn.close()
    print("\n✅ Banco resetado! Pronto para nova coleta.")

if __name__ == "__main__":
    print("=" * 60)
    print("RESET COMPLETO DO BANCO DE DADOS")
    print("=" * 60)
    print()
    print("⚠️  ATENÇÃO: Isso vai remover TODOS os dados!")
    print()
    
    confirm = input("Confirma reset completo? (s/N): ").strip().lower()
    if confirm == 's':
        reset_database()
    else:
        print("❌ Cancelado")