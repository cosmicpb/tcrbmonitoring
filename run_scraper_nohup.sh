#!/bin/bash
# Script para executar o scraper em background com nohup

echo "Iniciando scraper em background..."
echo "Logs serão salvos em: nohup.out e logs/scraper_*.log"
echo ""

# Executa com nohup, auto-respondendo 's' para as confirmações
nohup python3 -u run_scraper.py > nohup.out 2>&1 &

# Captura o PID
PID=$!

echo "✅ Scraper iniciado em background!"
echo "   PID: $PID"
echo ""
echo "📊 Para monitorar o progresso:"
echo "   tail -f nohup.out"
echo "   tail -f logs/scraper_*.log"
echo ""
echo "🛑 Para parar o scraper:"
echo "   kill $PID"
echo ""
echo "💾 Salvando PID em scraper.pid..."
echo $PID > scraper.pid

echo "✅ Pronto! O scraper está rodando em background."