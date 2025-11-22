#!/bin/bash
# Script para reiniciar coleta do zero

echo "============================================================"
echo "REINICIAR COLETA DO ZERO"
echo "============================================================"
echo ""

# 1. Parar scraper se estiver rodando
echo "🛑 Parando scraper..."
pkill -f robust_scraper.py 2>/dev/null
pkill -f run_scraper.py 2>/dev/null
sleep 2

if pgrep -f robust_scraper.py > /dev/null; then
    echo "   ⚠️  Scraper ainda rodando, forçando..."
    pkill -9 -f robust_scraper.py
    sleep 1
fi

echo "   ✅ Scraper parado"
echo ""

# 2. Limpar banco de dados
echo "💾 Limpando banco de dados..."
sqlite3 data/tcrb_observations.db "DELETE FROM observations; DELETE FROM sqlite_sequence WHERE name='observations';"
TOTAL=$(sqlite3 data/tcrb_observations.db "SELECT COUNT(*) FROM observations;")
echo "   ✅ Banco limpo (total: $TOTAL observações)"
echo ""

# 3. Remover checkpoints
echo "🗑️  Removendo checkpoints..."
rm -f data/scraper_checkpoint.json
rm -f data/failed_pages.json
rm -f scraper.pid
echo "   ✅ Checkpoints removidos"
echo ""

# 4. Verificar código corrigido
echo "🔍 Verificando código corrigido..."
if grep -q "obs-detail-tr" robust_scraper.py; then
    echo "   ✅ Código corrigido presente"
else
    echo "   ❌ ATENÇÃO: Código corrigido não encontrado!"
fi
echo ""

echo "============================================================"
echo "✅ PRONTO PARA REINICIAR!"
echo "============================================================"
echo ""
echo "Para iniciar a coleta:"
echo "  ./run_scraper_nohup.sh"
echo ""
echo "Ou manualmente:"
echo "  python3 robust_scraper.py"
echo ""