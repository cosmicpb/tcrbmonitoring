#!/usr/bin/env python3
"""
Script para migrar dados do SQLite local para D1 do Cloudflare
Migra de data/tcrb_observations.db para o banco D1
"""

import sqlite3
import json
import subprocess
import sys
import argparse
from datetime import datetime

# Configurações
SQLITE_DB = "data/tcrb_observations.db"
D1_DB_NAME = "tcrb-observations"  # Nome correto do D1
BATCH_SIZE = 100  # Batch otimizado (100 registros por vez)
TEST_MODE = False  # Modo produção: migração completa

def get_sqlite_data():
    """Lê dados do SQLite local"""
    print("📊 Conectando ao banco SQLite local...")
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    
    # Conta total
    cursor.execute("SELECT COUNT(*) FROM observations")
    total = cursor.fetchone()[0]
    print(f"✅ Total de observações no SQLite: {total:,}")
    
    # Busca todos os dados
    # Mapeia colunas do SQLite para o formato do D1
    cursor.execute("""
        SELECT
            star,
            jd,
            calendar_date,
            magnitude,
            error,
            band,
            observer,
            created_at
        FROM observations
        ORDER BY id
    """)
    
    data = cursor.fetchall()
    conn.close()
    
    return data, total

def check_d1_current_data():
    """Verifica dados atuais no D1"""
    print("\n📊 Verificando dados atuais no D1...")
    try:
        result = subprocess.run(
            ["npx", "wrangler", "d1", "execute", D1_DB_NAME, "--remote",
             "--command", "SELECT COUNT(*) as total FROM observations"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse da saída
        output = result.stdout
        if "total" in output:
            # Extrai o número da saída
            lines = output.strip().split('\n')
            for line in lines:
                if line.strip().isdigit():
                    current_total = int(line.strip())
                    print(f"✅ Total atual no D1: {current_total:,} observações")
                    return current_total
        
        print("⚠️  Não foi possível determinar o total atual no D1")
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao verificar D1: {e}")
        print(f"   Saída: {e.stdout}")
        print(f"   Erro: {e.stderr}")
        return 0

def create_insert_statement(batch):
    """Cria statement SQL para inserção em lote"""
    # Usa INSERT OR IGNORE para evitar duplicatas
    # Mapeia: band → filter, created_at → scraped_at
    sql = "INSERT OR IGNORE INTO observations (star, jd, calendar_date, magnitude, error, filter, observer, scraped_at) VALUES "
    
    values = []
    for row in batch:
        star, jd, calendar_date, mag, error, band, observer, created_at = row
        
        # Escapa aspas simples
        star = star.replace("'", "''") if star else 'T CrB'
        jd = jd.replace("'", "''") if jd else ''
        calendar_date = calendar_date.replace("'", "''") if calendar_date else ''
        band = band.replace("'", "''") if band else ''
        observer = observer.replace("'", "''") if observer else ''
        created_at = created_at.replace("'", "''") if created_at else ''
        
        # Converte magnitude e error para string
        mag_str = str(mag) if mag is not None else ''
        error_str = str(error) if error is not None else ''
        
        # Escapa aspas em magnitude e error
        mag_str = mag_str.replace("'", "''")
        error_str = error_str.replace("'", "''")
        
        values.append(
            f"('{star}', '{jd}', '{calendar_date}', '{mag_str}', '{error_str}', '{band}', '{observer}', '{created_at}')"
        )
    
    sql += ", ".join(values) + ";"
    return sql

def migrate_batch(batch, batch_num, total_batches):
    """Migra um lote de dados para o D1"""
    sql = create_insert_statement(batch)
    
    try:
        result = subprocess.run(
            ["npx", "wrangler", "d1", "execute", D1_DB_NAME, "--remote", "--command", sql],
            capture_output=True,
            text=True,
            check=True,
            timeout=60  # 60 segundos de timeout
        )
        
        return True, None
        
    except subprocess.TimeoutExpired:
        return False, "Timeout (60s)"
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else e.stdout
        return False, f"Exit {e.returncode}: {error_msg[:500]}"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:500]}"

def main():
    # Parse argumentos
    parser = argparse.ArgumentParser(description='Migra dados do SQLite para D1')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Pula confirmação (útil para execução automática)')
    args = parser.parse_args()
    
    print("=" * 70)
    print("MIGRAÇÃO DE DADOS: SQLite → D1")
    print("=" * 70)
    print()
    
    # Verifica dados atuais no D1
    current_d1_total = check_d1_current_data()
    
    # Lê dados do SQLite
    print()
    data, total = get_sqlite_data()
    
    if total == 0:
        print("❌ Nenhum dado encontrado no SQLite")
        sys.exit(1)
    
    # Calcula lotes
    total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
    
    print()
    print(f"📋 PLANO DE MIGRAÇÃO:")
    print(f"   Origem: {SQLITE_DB}")
    print(f"   Destino: D1 ({D1_DB_NAME})")
    print(f"   Total de registros: {total:,}")
    print(f"   Tamanho do lote: {BATCH_SIZE:,}")
    print(f"   Total de lotes: {total_batches:,}")
    print(f"   Dados atuais no D1: {current_d1_total:,}")
    print()
    
    # Confirmação (pula se --yes foi passado)
    if not args.yes:
        print("⚠️  ATENÇÃO:")
        print("   - A migração usará INSERT OR IGNORE (não duplicará dados)")
        print("   - Dados existentes no D1 serão preservados")
        print("   - O processo pode levar vários minutos")
        print()
        
        try:
            confirm = input("Deseja continuar? (s/N): ").strip().lower()
            if confirm != 's':
                print("❌ Migração cancelada")
                sys.exit(0)
        except EOFError:
            print("❌ Erro: Entrada não disponível. Use --yes para pular confirmação.")
            sys.exit(1)
    else:
        print("✅ Modo automático: pulando confirmação (--yes)")
    
    print()
    print("=" * 70)
    print("INICIANDO MIGRAÇÃO")
    print("=" * 70)
    print()
    
    # Migração
    start_time = datetime.now()
    success_count = 0
    error_count = 0
    
    # Modo de teste: apenas 1 lote
    total_to_process = BATCH_SIZE if TEST_MODE else total
    
    for i in range(0, total_to_process, BATCH_SIZE):
        batch_num = (i // BATCH_SIZE) + 1
        batch = data[i:i + BATCH_SIZE]
        
        print(f"Lote {batch_num}/{total_batches} ({len(batch)} registros)...", end=" ", flush=True)
        
        success, error = migrate_batch(batch, batch_num, total_batches)
        
        if success:
            success_count += len(batch)
            print(f"✅ OK")
        else:
            error_count += len(batch)
            print(f"❌ ERRO: {error}")
        
        # Progresso
        progress = (batch_num / total_batches) * 100
        elapsed = (datetime.now() - start_time).total_seconds()
        avg_time = elapsed / batch_num
        remaining = (total_batches - batch_num) * avg_time
        
        print(f"   Progresso: {progress:.1f}% | Tempo: {elapsed:.0f}s | Restante: ~{remaining:.0f}s")
        print()
    
    # Resumo
    total_time = (datetime.now() - start_time).total_seconds()
    
    print()
    print("=" * 70)
    print("MIGRAÇÃO FINALIZADA")
    print("=" * 70)
    print(f"✅ Registros processados com sucesso: {success_count:,}")
    if error_count > 0:
        print(f"❌ Registros com erro: {error_count:,}")
    print(f"⏱️  Tempo total: {total_time:.1f}s ({total_time/60:.1f}min)")
    print()
    
    # Verifica total final no D1
    print("Verificando total final no D1...")
    final_d1_total = check_d1_current_data()
    
    if final_d1_total > current_d1_total:
        new_records = final_d1_total - current_d1_total
        print(f"✅ Novos registros adicionados ao D1: {new_records:,}")
    
    print()
    print("Para verificar os dados no D1:")
    print(f"  npx wrangler d1 execute {D1_DB_NAME} --command \"SELECT COUNT(*) FROM observations\"")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Migração interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")
        sys.exit(1)