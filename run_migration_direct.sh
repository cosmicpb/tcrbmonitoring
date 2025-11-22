#!/bin/bash
################################################################################
# Script simplificado para executar migração diretamente
# Carrega NVM e executa Python com ambiente correto
################################################################################

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}🚀 Migração JD Numeric (Direto)${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Carrega NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Verifica Node
NODE_VERSION=$(node --version 2>/dev/null || echo "none")
echo -e "${GREEN}✅ Node.js: $NODE_VERSION${NC}"

if [ "$NODE_VERSION" = "none" ]; then
    echo -e "${RED}❌ Node.js não encontrado!${NC}"
    exit 1
fi

# Executa migração diretamente (sem nohup)
echo -e "${BLUE}🔧 Executando migração...${NC}"
echo ""

python3 migrate_jd_to_numeric.py --yes

echo ""
echo -e "${GREEN}✅ Concluído!${NC}"