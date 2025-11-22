#!/bin/bash
# Script para verificar o status da migração

echo "============================================================"
echo "STATUS DA MIGRAÇÃO: SQLite → D1"
echo "============================================================"
echo ""

# Verifica se está rodando
if [ -f "migration.pid" ]; then
    PID=$(cat migration.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ Migração está RODANDO (PID: $PID)"
        
        # Tempo de execução
        START_TIME=$(ps -o lstart= -p $PID)
        echo "   Iniciada em: $START_TIME"
        
        # Uso de CPU e memória
        CPU=$(ps -p $PID -o %cpu= | xargs)
        MEM=$(ps -p $PID -o %mem= | xargs)
        echo "   CPU: ${CPU}% | Memória: ${MEM}%"
    else
        echo "❌ Migração NÃO está rodando (PID antigo: $PID)"
        echo "   O processo pode ter terminado ou falhado"
    fi
else
    echo "⚪ Nenhuma migração em execução"
fi

echo ""

# Verifica log
if [ -f "migration.log" ]; then
    echo "📄 LOG DA MIGRAÇÃO:"
    echo "-----------------------------------------------------------"
    
    # Últimas 15 linhas do log
    tail -15 migration.log
    
    echo "-----------------------------------------------------------"
    echo ""
    
    # Estatísticas do log
    TOTAL_LINES=$(wc -l < migration.log)
    LOTES_OK=$(grep -c "✅ OK" migration.log 2>/dev/null || echo "0")
    LOTES_ERRO=$(grep -c "❌ ERRO" migration.log 2>/dev/null || echo "0")
    
    echo "📊 Estatísticas:"
    echo "   Linhas no log: $TOTAL_LINES"
    echo "   Lotes OK: $LOTES_OK"
    echo "   Lotes com erro: $LOTES_ERRO"
    
    # Última linha de progresso
    LAST_PROGRESS=$(grep "Progresso:" migration.log | tail -1)
    if [ ! -z "$LAST_PROGRESS" ]; then
        echo "   $LAST_PROGRESS"
    fi
else
    echo "⚠️  Arquivo de log não encontrado: migration.log"
fi

echo ""

# Verifica dados no D1
echo "🔍 Verificando dados no D1..."
STATS=$(curl -s "https://tcrb-api.pbaldacimjr.workers.dev/stats" 2>/dev/null)

if [ $? -eq 0 ]; then
    TOTAL=$(echo "$STATS" | python3 -c "import sys, json; print(json.load(sys.stdin)['statistics']['total_observations'])" 2>/dev/null || echo "?")
    LATEST=$(echo "$STATS" | python3 -c "import sys, json; print(json.load(sys.stdin)['statistics']['latest_observation']['date'])" 2>/dev/null || echo "?")
    
    echo "   Total no D1: $TOTAL observações"
    echo "   Última observação: $LATEST"
else
    echo "   ⚠️  Não foi possível consultar a API"
fi

echo ""

# Comandos úteis
echo "💡 COMANDOS ÚTEIS:"
echo "   Monitorar em tempo real:"
echo "     tail -f migration.log"
echo ""
echo "   Parar migração:"
if [ -f "migration.pid" ]; then
    PID=$(cat migration.pid)
    echo "     kill $PID && rm migration.pid"
else
    echo "     (nenhuma migração rodando)"
fi
echo ""
echo "   Verificar API:"
echo "     curl https://tcrb-api.pbaldacimjr.workers.dev/stats | python3 -m json.tool"
echo ""