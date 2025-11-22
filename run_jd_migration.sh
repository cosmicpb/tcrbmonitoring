#!/bin/bash
################################################################################
# Script para executar migração jd_numeric em background com nohup
# Uso: ./run_jd_migration.sh
################################################################################

set -e  # Para em caso de erro

# Carrega NVM se disponível
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Arquivos
PYTHON_SCRIPT="migrate_jd_to_numeric.py"
LOG_FILE="migration_jd_numeric.log"
PID_FILE="migration_jd_numeric.pid"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}🚀 Migração JD Numeric${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Verifica se Python script existe
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo -e "${RED}❌ Erro: $PYTHON_SCRIPT não encontrado!${NC}"
    exit 1
fi

# Verifica se já está rodando
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Migração já está rodando (PID: $OLD_PID)${NC}"
        echo ""
        echo "Para ver o progresso:"
        echo -e "${GREEN}tail -f $LOG_FILE${NC}"
        echo ""
        echo "Para parar a migração:"
        echo -e "${RED}kill $OLD_PID${NC}"
        exit 1
    else
        echo -e "${YELLOW}⚠️  Removendo PID file antigo...${NC}"
        rm -f "$PID_FILE"
    fi
fi

# Verifica Node.js e npx
NODE_VERSION=$(node --version 2>/dev/null || echo "none")
if [ "$NODE_VERSION" = "none" ]; then
    echo -e "${RED}❌ Erro: Node.js não está instalado!${NC}"
    echo ""
    echo "Instale com NVM:"
    echo -e "${GREEN}curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash${NC}"
    echo -e "${GREEN}nvm install 20${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Node.js: $NODE_VERSION${NC}"

# Verifica se npx está disponível
if ! command -v npx &> /dev/null; then
    echo -e "${RED}❌ Erro: npx não encontrado!${NC}"
    exit 1
fi

# Verifica se está logado no Cloudflare (não bloqueia se falhar)
echo -e "${BLUE}🔐 Verificando autenticação Cloudflare...${NC}"
if npx wrangler whoami &> /dev/null 2>&1; then
    echo -e "${GREEN}✅ Autenticado no Cloudflare${NC}"
else
    echo -e "${YELLOW}⚠️  Aviso: Não foi possível verificar autenticação${NC}"
    echo ""
    echo "Se houver erro durante migração, faça login com:"
    echo -e "${GREEN}npx wrangler login${NC}"
    echo ""
    read -p "Continuar mesmo assim? (s/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}✅ Pré-requisitos verificados${NC}"
echo ""

# Mostra informações
echo -e "${BLUE}📋 Informações:${NC}"
echo "   Script: $PYTHON_SCRIPT"
echo "   Log: $LOG_FILE"
echo "   PID: $PID_FILE"
echo ""

# Confirmação
echo -e "${YELLOW}⚠️  Esta migração irá:${NC}"
echo "   1. Adicionar coluna jd_numeric ao D1"
echo "   2. Migrar ~90.000 registros"
echo "   3. Criar 2 índices otimizados"
echo "   4. Tempo estimado: 2-5 minutos"
echo ""

read -p "Deseja continuar? (s/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo -e "${RED}❌ Migração cancelada${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}🔧 Iniciando Migração${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Remove log antigo se existir
if [ -f "$LOG_FILE" ]; then
    echo -e "${YELLOW}⚠️  Removendo log antigo...${NC}"
    rm -f "$LOG_FILE"
fi

# Inicia migração em background com nohup
echo -e "${GREEN}🚀 Iniciando migração em background...${NC}"
echo ""

# Usa argumento --yes para pular confirmações
nohup python3 "$PYTHON_SCRIPT" --yes > "$LOG_FILE" 2>&1 &
MIGRATION_PID=$!

# Salva PID
echo "$MIGRATION_PID" > "$PID_FILE"

echo -e "${GREEN}✅ Migração iniciada!${NC}"
echo ""
echo -e "${BLUE}📊 Status:${NC}"
echo "   PID: $MIGRATION_PID"
echo "   Log: $LOG_FILE"
echo ""

# Aguarda um pouco para verificar se não falhou imediatamente
sleep 2

if ! ps -p "$MIGRATION_PID" > /dev/null 2>&1; then
    echo -e "${RED}❌ Migração falhou ao iniciar!${NC}"
    echo ""
    echo "Últimas linhas do log:"
    tail -20 "$LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi

echo -e "${GREEN}✅ Migração rodando em background${NC}"
echo ""
echo -e "${BLUE}📝 Comandos úteis:${NC}"
echo ""
echo "Ver progresso em tempo real:"
echo -e "${GREEN}tail -f $LOG_FILE${NC}"
echo ""
echo "Ver últimas 50 linhas:"
echo -e "${GREEN}tail -50 $LOG_FILE${NC}"
echo ""
echo "Verificar se está rodando:"
echo -e "${GREEN}ps -p $MIGRATION_PID${NC}"
echo ""
echo "Parar migração (NÃO RECOMENDADO):"
echo -e "${RED}kill $MIGRATION_PID${NC}"
echo ""
echo "Verificar resultado final:"
echo -e "${GREEN}cat $LOG_FILE | grep -A 10 'MIGRAÇÃO CONCLUÍDA'${NC}"
echo ""

# Mostra início do log
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}📄 Início do Log${NC}"
echo -e "${BLUE}================================${NC}"
sleep 1
head -30 "$LOG_FILE" 2>/dev/null || echo "Aguardando log..."

echo ""
echo -e "${YELLOW}💡 Dica: Use 'tail -f $LOG_FILE' para acompanhar o progresso${NC}"
echo ""