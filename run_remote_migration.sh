#!/bin/bash

# Script para executar migração no banco REMOTO
# Migra 629.561 registros em lotes de 5000

echo "======================================================================"
echo "🚀 MIGRAÇÃO REMOTA: Populando jd_numeric"
echo "======================================================================"
echo ""
echo "⚠️  ATENÇÃO: Esta migração irá:"
echo "   - Processar 629.561 registros no banco REMOTO"
echo "   - Executar ~126 lotes de 5000 registros"
echo "   - Tempo estimado: 5-10 minutos"
echo ""
read -p "Deseja continuar? (s/N): " confirm

if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
    echo "❌ Migração cancelada"
    exit 1
fi

echo ""
echo "✅ Iniciando migração..."
echo ""

# Executa script Python com flag --yes
python3 migrate_jd_to_numeric.py --yes

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "======================================================================"
    echo "✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!"
    echo "======================================================================"
else
    echo ""
    echo "======================================================================"
    echo "❌ MIGRAÇÃO FALHOU (exit code: $exit_code)"
    echo "======================================================================"
fi

exit $exit_code