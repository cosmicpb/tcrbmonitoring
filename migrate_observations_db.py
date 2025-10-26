#!/usr/bin/env python3
"""
Script para migrar o banco de dados observations.db
Adiciona a coluna obs_type se ela não existir
"""

import sqlite3
import os

DB_PATH = "data/tcrb_observations.db"

def migrate_database():
    if not os.path.exists(DB_PATH):
        print(f"❌ Banco de dados não encontrado: {DB_PATH}")
        return
    
    print(f"Migrando banco de dados: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verifica se a coluna obs_type já existe
    cursor.execute("PRAGMA table_info(observations)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'obs_type' in columns:
        print("✅ Coluna obs_type já existe. Nenhuma migração necessária.")
    else:
        print("Adicionando coluna obs_type...")
        try:
            cursor.execute("ALTER TABLE observations ADD COLUMN obs_type TEXT")
            conn.commit()
            print("✅ Coluna obs_type adicionada com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao adicionar coluna: {e}")
            conn.rollback()
    
    # Mostra estatísticas
    cursor.execute("SELECT COUNT(*) FROM observations")
    total = cursor.fetchone()[0]
    print(f"\n📊 Total de observações no banco: {total:,}")
    
    conn.close()

if __name__ == "__main__":
    migrate_database()