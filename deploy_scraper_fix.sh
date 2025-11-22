#!/bin/bash
# Script para fazer deploy do scraper corrigido na Cloudflare
#
# CORREÇÃO APLICADA:
# - Remove células vazias antes de acessar dados
# - Remove "Details..." do campo observer
# - Usa índices relativos (não fixos)

echo "============================================================"
echo "DEPLOY DO SCRAPER CORRIGIDO - Cloudflare Workers"
echo "============================================================"
echo ""

# Seta Node.js v20 se disponível
if command -v nvm &> /dev/null; then
    echo "🔧 Usando nvm para setar Node.js v20..."
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm use 20 2>/dev/null || nvm use default
elif [ -x "/usr/bin/node" ]; then
    # Usa node do sistema
    export PATH="/usr/bin:$PATH"
fi

# Verifica versão do Node.js
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
echo "📦 Node.js versão: $(node --version)"

if [ "$NODE_VERSION" -lt 20 ]; then
    echo ""
    echo "❌ ERRO: Wrangler requer Node.js v20.0.0 ou superior"
    echo "   Versão atual: $(node --version)"
    echo ""
    echo "Para atualizar o Node.js:"
    echo ""
    echo "Opção 1 - Usando nvm (recomendado):"
    echo "  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
    echo "  source ~/.bashrc"
    echo "  nvm install 20"
    echo "  nvm use 20"
    echo ""
    echo "Opção 2 - Usando apt (Ubuntu/Debian):"
    echo "  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
    echo "  sudo apt-get install -y nodejs"
    echo ""
    echo "Depois de atualizar, execute este script novamente."
    exit 1
fi

echo "✅ Node.js versão compatível"
echo ""

# Verifica se o arquivo foi modificado
echo "🔍 Verificando correções aplicadas..."
if grep -q "non_empty_cells" scraper-worker.py; then
    echo "   ✅ Correção presente: remove células vazias"
else
    echo "   ❌ ATENÇÃO: Correção não encontrada!"
    exit 1
fi

if grep -q "Details" scraper-worker.py; then
    echo "   ✅ Correção presente: remove 'Details...'"
else
    echo "   ❌ ATENÇÃO: Correção não encontrada!"
    exit 1
fi

echo ""
echo "📋 Resumo das correções:"
echo "   • Remove células vazias do início da linha"
echo "   • Usa índices relativos (não fixos)"
echo "   • Remove 'Details...' do campo observer"
echo "   • Valida número mínimo de células (7)"
echo ""

# Confirma deploy
read -p "Fazer deploy do scraper corrigido? (s/N): " confirm
if [ "$confirm" != "s" ]; then
    echo "❌ Deploy cancelado"
    exit 0
fi

echo ""
echo "🚀 Fazendo deploy..."
echo ""

# Deploy
npx wrangler deploy --config wrangler-scraper.toml

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✅ DEPLOY CONCLUÍDO COM SUCESSO!"
    echo "============================================================"
    echo ""
    echo "O scraper corrigido está agora ativo na Cloudflare."
    echo "Ele será executado automaticamente a cada hora via Cron Trigger."
    echo ""
    echo "Para testar manualmente:"
    echo "  npx wrangler tail --config wrangler-scraper.toml"
    echo ""
else
    echo ""
    echo "❌ Erro durante o deploy"
    exit 1
fi