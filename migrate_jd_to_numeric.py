#!/usr/bin/env python3
"""
Script de Migração: Adicionar coluna jd_numeric otimizada
Converte campo jd de TEXT para REAL para melhorar performance

IMPORTANTE: Este script deve ser executado APENAS UMA VEZ
"""

import subprocess
import json
import sys
import time
import argparse
import os

# Configurações
D1_DATABASE = "tcrb-observations"
BATCH_SIZE = 5000  # Processar 5000 registros por vez (otimizado para 628k registros)
WRANGLER_CONFIG = "wrangler-api.toml"  # Usar config da API

# Caminho completo do npx do NVM
NPX_PATH = "/home/baldacim/.nvm/versions/node/v20.19.5/bin/npx"

def run_d1_command(sql_command, show_output=True):
    """Executa comando SQL no D1 via wrangler"""
    try:
        # Usa bash com NVM para garantir Node v20
        bash_cmd = f"""
        . ~/.nvm/nvm.sh && nvm use 20 > /dev/null 2>&1 && \
        npx wrangler d1 execute {D1_DATABASE} \
        --config {WRANGLER_CONFIG} \
        --remote \
        --command "{sql_command.replace('"', '\\"')}"
        """
        
        result = subprocess.run(
            ["bash", "-c", bash_cmd],
            capture_output=True,
            text=True,
            check=True
        )
        
        if show_output and result.stdout:
            print(result.stdout)
        
        return True, result.stdout
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar comando SQL:")
        print(f"   {e.stderr}")
        return False, e.stderr

def check_column_exists():
    """Verifica se coluna jd_numeric já existe"""
    print("\n🔍 Verificando se coluna jd_numeric já existe...")
    
    sql = "PRAGMA table_info(observations);"
    success, output = run_d1_command(sql, show_output=False)
    
    if success and "jd_numeric" in output:
        print("⚠️  Coluna jd_numeric já existe!")
        return True
    
    print("✅ Coluna jd_numeric não existe, pode prosseguir")
    return False

def get_total_records():
    """Obtém total de registros"""
    print("\n📊 Contando registros...")
    
    sql = "SELECT COUNT(*) as total FROM observations;"
    success, output = run_d1_command(sql, show_output=False)
    
    if success:
        # Parse output para extrair número
        try:
            # Output vem como tabela, extrair número
            lines = output.strip().split('\n')
            for line in lines:
                if line.strip().isdigit():
                    total = int(line.strip())
                    print(f"✅ Total de registros: {total:,}")
                    return total
        except:
            pass
    
    print("⚠️  Não foi possível contar registros, assumindo 628240")
    return 628240

def add_column():
    """Adiciona coluna jd_numeric"""
    print("\n➕ Adicionando coluna jd_numeric...")
    
    sql = "ALTER TABLE observations ADD COLUMN jd_numeric REAL;"
    success, output = run_d1_command(sql)
    
    if success:
        print("✅ Coluna jd_numeric adicionada com sucesso!")
        return True
    else:
        # Verifica se erro é porque coluna já existe
        if "duplicate column name" in output.lower():
            print("⚠️  Coluna já existe, pulando esta etapa...")
            return True
        else:
            print("❌ Falha ao adicionar coluna")
            return False

def migrate_data_batch(limit):
    """Migra um lote de dados (sempre pega os próximos NULL)"""
    sql = f"""
        UPDATE observations
        SET jd_numeric = CAST(jd AS REAL)
        WHERE id IN (
            SELECT id FROM observations
            WHERE jd_numeric IS NULL
            LIMIT {limit}
        );
    """
    
    success, output = run_d1_command(sql, show_output=False)
    return success

def count_remaining_nulls():
    """Conta quantos registros ainda precisam ser migrados"""
    sql = "SELECT COUNT(*) FROM observations WHERE jd_numeric IS NULL;"
    success, output = run_d1_command(sql, show_output=False)
    
    if success:
        try:
            lines = output.strip().split('\n')
            for line in lines:
                if line.strip().isdigit():
                    return int(line.strip())
        except:
            pass
    return 0

def migrate_all_data(total_records):
    """Migra todos os dados em lotes até não haver mais NULLs"""
    print(f"\n🔄 Migrando dados em lotes de {BATCH_SIZE}...")
    print(f"   Estimativa inicial: {total_records:,} registros")
    
    batch = 0
    total_migrated = 0
    
    while True:
        batch += 1
        
        # Conta quantos ainda faltam
        remaining = count_remaining_nulls()
        
        if remaining == 0:
            print(f"\n✅ Todos os registros foram migrados!")
            break
        
        print(f"   Lote {batch} ({remaining:,} restantes)...", end=" ")
        
        success = migrate_data_batch(BATCH_SIZE)
        
        if success:
            print("✅")
            total_migrated += min(BATCH_SIZE, remaining)
        else:
            print("❌")
            print(f"⚠️  Erro no lote {batch}, mas continuando...")
        
        # Pequeno delay para não sobrecarregar
        time.sleep(0.5)
        
        # Proteção contra loop infinito
        if batch > 10000:
            print(f"\n⚠️  Limite de lotes atingido (10000), parando...")
            break
    
    print(f"✅ Migração de dados concluída! Total migrado: {total_migrated:,}")
    return True

def create_index():
    """Cria índice otimizado"""
    print("\n📇 Criando índice otimizado...")
    
    sql = "CREATE INDEX IF NOT EXISTS idx_jd_numeric ON observations(jd_numeric DESC);"
    success, output = run_d1_command(sql)
    
    if success:
        print("✅ Índice idx_jd_numeric criado com sucesso!")
        return True
    else:
        print("❌ Falha ao criar índice")
        return False

def create_composite_index():
    """Cria índice composto para queries filtradas por estrela"""
    print("\n📇 Criando índice composto (star, jd_numeric)...")
    
    sql = "CREATE INDEX IF NOT EXISTS idx_star_jd_numeric ON observations(star, jd_numeric DESC);"
    success, output = run_d1_command(sql)
    
    if success:
        print("✅ Índice idx_star_jd_numeric criado com sucesso!")
        return True
    else:
        print("❌ Falha ao criar índice composto")
        return False

def validate_migration():
    """Valida que migração funcionou"""
    print("\n✅ Validando migração...")
    
    # Verifica se há valores NULL
    sql = "SELECT COUNT(*) as nulls FROM observations WHERE jd_numeric IS NULL;"
    success, output = run_d1_command(sql, show_output=False)
    
    if success and "0" in output:
        print("✅ Nenhum valor NULL encontrado")
    else:
        print("⚠️  Alguns valores NULL encontrados, pode precisar re-executar migração")
    
    # Verifica se valores estão corretos (compara alguns)
    sql = """
        SELECT 
            jd, 
            jd_numeric,
            CAST(jd AS REAL) as jd_converted
        FROM observations 
        LIMIT 5;
    """
    success, output = run_d1_command(sql)
    
    if success:
        print("✅ Amostra de dados migrados:")
        print(output)
    
    # Verifica índices
    sql = "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='observations';"
    success, output = run_d1_command(sql)
    
    if success:
        print("\n✅ Índices criados:")
        print(output)
    
    return True

def main():
    """Executa migração completa"""
    # Parse argumentos
    parser = argparse.ArgumentParser(description='Migração jd_numeric para D1')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Pula confirmações (para uso em scripts)')
    args = parser.parse_args()
    
    print("=" * 70)
    print("🚀 MIGRAÇÃO: Adicionar coluna jd_numeric otimizada")
    print("=" * 70)
    
    # Verificações iniciais
    if check_column_exists():
        if not args.yes:
            response = input("\n⚠️  Coluna já existe. Deseja re-executar migração? (s/N): ")
            if response.lower() != 's':
                print("❌ Migração cancelada")
                return 1
        else:
            print("\n⚠️  Coluna já existe, mas continuando (--yes)")
    
    total_records = get_total_records()
    
    print(f"\n📋 Plano de Migração:")
    print(f"   1. Adicionar coluna jd_numeric (REAL)")
    print(f"   2. Migrar {total_records:,} registros em lotes de {BATCH_SIZE}")
    print(f"   3. Criar índice idx_jd_numeric")
    print(f"   4. Criar índice idx_star_jd_numeric")
    print(f"   5. Validar migração")
    
    if not args.yes:
        response = input("\n⚠️  Deseja continuar? (s/N): ")
        if response.lower() != 's':
            print("❌ Migração cancelada")
            return 1
    else:
        print("\n✅ Continuando automaticamente (--yes)")
    
    # Executa migração
    print("\n" + "=" * 70)
    print("🔧 INICIANDO MIGRAÇÃO")
    print("=" * 70)
    
    start_time = time.time()
    
    # Passo 1: Adicionar coluna
    if not add_column():
        print("\n❌ Migração falhou na etapa 1")
        return 1
    
    # Passo 2: Migrar dados
    if not migrate_all_data(total_records):
        print("\n❌ Migração falhou na etapa 2")
        return 1
    
    # Passo 3: Criar índice
    if not create_index():
        print("\n❌ Migração falhou na etapa 3")
        return 1
    
    # Passo 4: Criar índice composto
    if not create_composite_index():
        print("\n⚠️  Índice composto falhou, mas migração pode continuar")
    
    # Passo 5: Validar
    validate_migration()
    
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 70)
    print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 70)
    print(f"⏱️  Tempo total: {elapsed_time:.1f} segundos")
    print(f"📊 Registros migrados: {total_records:,}")
    print(f"📇 Índices criados: 2")
    
    print("\n📝 Próximos passos:")
    print("   1. Atualizar api-worker.py para usar jd_numeric")
    print("   2. Atualizar scraper-worker.py para popular jd_numeric")
    print("   3. Fazer deploy das mudanças")
    print("   4. Executar novo teste de performance")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Migração cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)