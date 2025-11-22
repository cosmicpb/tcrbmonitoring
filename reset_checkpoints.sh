#!/bin/bash
# Script para remover checkpoints e recoletar dados faltantes
# Mantém os dados atuais no banco - duplicatas serão ignoradas automaticamente

echo "============================================================"
echo "RESET DE CHECKPOINTS - Manter Dados Atuais"
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

# 2. Verificar dados atuais
echo "💾 Verificando dados atuais..."
TOTAL=$(sqlite3 data/tcrb_observations.db "SELECT COUNT(*) FROM observations;" 2>/dev/null || echo "0")
echo "   📊 Total atual: $TOTAL observações"
echo ""

# 3. Remover apenas checkpoints
echo "🗑️  Removendo checkpoints..."
rm -f data/scraper_checkpoint.json
rm -f data/failed_pages.json
rm -f scraper.pid
echo "   ✅ Checkpoints removidos"
echo ""

# 4. Verificar código corrigido
echo "🔍 Verificando código corrigido..."
if grep -q "non_empty_cols" robust_scraper.py; then
    echo "   ✅ Código corrigido presente (remove células vazias)"
else
    echo "   ❌ ATENÇÃO: Código corrigido não encontrado!"
fi
echo ""

echo "============================================================"
echo "✅ PRONTO PARA RECOLETAR!"
echo "============================================================"
echo ""
echo "ℹ️  O scraper vai:"
echo "   • Recoletar todas as 3.608 páginas"
echo "   • Manter os $TOTAL registros atuais"
echo "   • Adicionar apenas observações faltantes (~5.147)"
echo "   • Ignorar duplicatas automaticamente (INSERT OR IGNORE)"
echo ""
echo "Para iniciar a coleta:"
echo "  ./run_scraper_nohup.sh"
echo ""
echo "Ou manualmente:"
echo "  python3 robust_scraper.py"
echo ""