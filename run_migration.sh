#!/bin/bash
# Script para executar migração de dados SQLite → D1 em background
# Usa nohup para continuar executando mesmo após logout

echo "============================================================"
echo "MIGRAÇÃO DE DADOS: SQLite → D1 (Background)"
echo "============================================================"
echo ""

# Verifica se Python está disponível
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado"
    exit 1
fi

# Verifica se o script de migração existe
if [ ! -f "migrate_to_d1.py" ]; then
    echo "❌ Script migrate_to_d1.py não encontrado"
    exit 1
fi

# Verifica se o banco SQLite existe
if [ ! -f "data/tcrb_observations.db" ]; then
    echo "❌ Banco SQLite não encontrado: data/tcrb_observations.db"
    exit 1
fi

# Verifica se já está rodando
if [ -f "migration.pid" ]; then
    PID=$(cat migration.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  Migração já está em execução (PID: $PID)"
        echo ""
        echo "Para verificar o progresso:"
        echo "  tail -f migration.log"
        echo ""
        echo "Para parar a migração:"
        echo "  kill $PID"
        exit 1
    else
        echo "🗑️  Removendo PID antigo..."
        rm -f migration.pid
    fi
fi

# Informações
echo "📊 Informações:"
TOTAL=$(sqlite3 data/tcrb_observations.db "SELECT COUNT(*) FROM observations;" 2>/dev/null || echo "?")
echo "   Total de observações: $TOTAL"
echo "   Batch size: 100 registros"
echo "   Tempo estimado: ~4-5 horas"
echo ""

# Confirma
read -p "Iniciar migração em background? (s/N): " confirm
if [ "$confirm" != "s" ]; then
    echo "❌ Cancelado"
    exit 0
fi

echo ""
echo "🚀 Iniciando migração em background..."
echo ""

# Ativa ambiente virtual se existir
if [ -d "venv" ]; then
    echo "🔧 Ativando ambiente virtual..."
    source venv/bin/activate
fi

# Configura Node.js v20 se nvm estiver disponível
if [ -d "$HOME/.nvm" ]; then
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm use 20 &> /dev/null || true
fi

# Executa migração em background com flag --yes
nohup python3 migrate_to_d1.py --yes > migration.log 2>&1 &
PID=$!

# Salva PID
echo $PID > migration.pid

echo "✅ Migração iniciada!"
echo ""
echo "📋 Informações:"
echo "   PID: $PID"
echo "   Log: migration.log"
echo "   PID file: migration.pid"
echo ""
echo "📊 Para monitorar o progresso:"
echo "   tail -f migration.log"
echo ""
echo "🔍 Para verificar se está rodando:"
echo "   ps -p $PID"
echo ""
echo "⏹️  Para parar a migração:"
echo "   kill $PID"
echo "   rm migration.pid"
echo ""
echo "📈 Para verificar dados no D1:"
echo "   curl https://tcrb-api.pbaldacimjr.workers.dev/stats"
echo ""

# Aguarda 2 segundos e mostra início do log
sleep 2
if [ -f "migration.log" ]; then
    echo "📄 Primeiras linhas do log:"
    echo "-----------------------------------------------------------"
    head -20 migration.log
    echo "-----------------------------------------------------------"
    echo ""
    echo "💡 Use 'tail -f migration.log' para acompanhar em tempo real"
fi