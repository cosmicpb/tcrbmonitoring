#!/usr/bin/env python3
"""
Script para limpar dados corrompidos do banco SQLite.
Remove observações que contêm cabeçalhos de tabela ao invés de dados reais.
"""

import sqlite3

DB_PATH = "data/tcrb_observations.db"

def clean_corrupted_data():
    """Remove dados corrompidos do banco"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Conta total antes
    cursor.execute("SELECT COUNT(*) FROM observations")
    total_before = cursor.fetchone()[0]
    print(f"📊 Total de registros antes: {total_before:,}")
    
    # Identifica registros corrompidos (contêm palavras-chave de cabeçalho)
    # Os dados corrompidos estão principalmente na coluna date_br
    header_keywords = ['Comp Star', 'Check Star', 'Transformed', 'Chart', 'Comment Codes']
    
    corrupted_count = 0
    for keyword in header_keywords:
        cursor.execute("""
            SELECT COUNT(*) FROM observations
            WHERE date_br LIKE ? OR star LIKE ? OR observer LIKE ? OR obs_type LIKE ?
        """, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
        count = cursor.fetchone()[0]
        corrupted_count += count
        print(f"   ├─ Registros com '{keyword}': {count:,}")
    
    print(f"\n⚠️  Total de registros corrompidos identificados: {corrupted_count:,}")
    print(f"✅ Registros válidos: {total_before - corrupted_count:,}")
    print()
    
    # Confirmação
    confirm = input("Deseja deletar os registros corrompidos? (s/N): ").strip().lower()
    if confirm != 's':
        print("❌ Operação cancelada")
        conn.close()
        return
    
    # Deleta registros corrompidos
    print("\n🗑️  Deletando registros corrompidos...")
    for keyword in header_keywords:
        cursor.execute("""
            DELETE FROM observations
            WHERE date_br LIKE ? OR star LIKE ? OR observer LIKE ? OR obs_type LIKE ?
        """, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
        deleted = cursor.rowcount
        if deleted > 0:
            print(f"   ├─ Deletados com '{keyword}': {deleted:,}")
    
    conn.commit()
    
    # Conta total depois
    cursor.execute("SELECT COUNT(*) FROM observations")
    total_after = cursor.fetchone()[0]
    
    print(f"\n✅ Limpeza concluída!")
    print(f"   ├─ Registros antes: {total_before:,}")
    print(f"   ├─ Registros deletados: {total_before - total_after:,}")
    print(f"   └─ Registros restantes: {total_after:,}")
    
    # Otimiza banco
    print("\n🔧 Otimizando banco de dados...")
    cursor.execute("VACUUM")
    print("✅ Banco otimizado!")
    
    conn.close()

if __name__ == "__main__":
    try:
        clean_corrupted_data()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operação cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")