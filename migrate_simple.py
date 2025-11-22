#!/usr/bin/env python3
"""
Migração Simplificada: Executa UPDATE único para migrar todos os registros
"""

import subprocess
import time

def run_command(sql, description):
    """Executa comando SQL no banco remoto"""
    print(f"\n{description}...")
    
    bash_cmd = f"""
    . ~/.nvm/nvm.sh && nvm use 20 > /dev/null 2>&1 && \
    npx wrangler d1 execute tcrb-observations \
    --config wrangler-api.toml \
    --remote \
    --command "{sql}"
    """
    
    start = time.time()
    result = subprocess.run(
        ["bash", "-c", bash_cmd],
        capture_output=True,
        text=True
    )
    elapsed = time.time() - start
    
    print(f"⏱️  Tempo: {elapsed:.1f}s")
    print(f"Exit code: {result.returncode}")
    
    if result.returncode == 0:
        print("✅ Sucesso!")
        return True
    else:
        print(f"❌ Erro:\n{result.stderr}")
        return False

print("=" * 70)
print("🚀 MIGRAÇÃO SIMPLIFICADA: jd_numeric")
print("=" * 70)

# 1. Verificar quantos NULLs existem
print("\n📊 Verificando registros com NULL...")
run_command(
    "SELECT COUNT(*) as nulls FROM observations WHERE jd_numeric IS NULL;",
    "Contando NULLs"
)

# 2. Executar UPDATE único (pode demorar alguns minutos)
print("\n" + "=" * 70)
print("🔄 EXECUTANDO MIGRAÇÃO COMPLETA")
print("=" * 70)
print("\n⚠️  ATENÇÃO: Isto pode demorar 5-10 minutos!")
print("   Processando 629.561 registros em uma única transação...")

success = run_command(
    "UPDATE observations SET jd_numeric = CAST(jd AS REAL) WHERE jd_numeric IS NULL;",
    "Migrando TODOS os registros"
)

if not success:
    print("\n❌ Migração falhou!")
    exit(1)

# 3. Verificar resultado
print("\n" + "=" * 70)
print("✅ VALIDANDO RESULTADO")
print("=" * 70)

run_command(
    "SELECT COUNT(*) as nulls FROM observations WHERE jd_numeric IS NULL;",
    "Verificando NULLs restantes"
)

run_command(
    "SELECT COUNT(*) as migrated FROM observations WHERE jd_numeric IS NOT NULL;",
    "Verificando registros migrados"
)

run_command(
    "SELECT jd, jd_numeric, CAST(jd AS REAL) as converted FROM observations LIMIT 5;",
    "Amostra de dados"
)

print("\n" + "=" * 70)
print("✅ MIGRAÇÃO CONCLUÍDA!")
print("=" * 70)