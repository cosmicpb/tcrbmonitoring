#!/usr/bin/env python3
"""
Teste rápido: Verifica conexão com banco remoto e adiciona coluna jd_numeric
"""

import subprocess
import sys

def run_remote_command(sql):
    """Executa comando no banco REMOTO"""
    bash_cmd = f"""
    . ~/.nvm/nvm.sh && nvm use 20 > /dev/null 2>&1 && \
    npx wrangler d1 execute tcrb-observations \
    --config wrangler-api.toml \
    --remote \
    --command "{sql}"
    """
    
    result = subprocess.run(
        ["bash", "-c", bash_cmd],
        capture_output=True,
        text=True
    )
    
    print(f"Exit code: {result.returncode}")
    print(f"Output:\n{result.stdout}")
    if result.stderr:
        print(f"Errors:\n{result.stderr}")
    
    return result.returncode == 0

print("=" * 70)
print("TESTE: Conexão com banco REMOTO")
print("=" * 70)

print("\n1. Contando registros...")
if run_remote_command("SELECT COUNT(*) as total FROM observations;"):
    print("✅ Conexão OK")
else:
    print("❌ Falha na conexão")
    sys.exit(1)

print("\n2. Verificando se coluna jd_numeric existe...")
if run_remote_command("PRAGMA table_info(observations);"):
    print("✅ Schema obtido")
else:
    print("❌ Falha ao obter schema")
    sys.exit(1)

print("\n3. Tentando adicionar coluna jd_numeric...")
if run_remote_command("ALTER TABLE observations ADD COLUMN jd_numeric REAL;"):
    print("✅ Coluna adicionada!")
else:
    print("⚠️ Pode já existir ou houve erro")

print("\n4. Verificando novamente o schema...")
run_remote_command("PRAGMA table_info(observations);")

print("\n" + "=" * 70)
print("Teste concluído!")
print("=" * 70)