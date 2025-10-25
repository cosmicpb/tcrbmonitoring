import { monitor } from './index.js';

/**
 * Scheduler para execução periódica do monitoramento
 * Este script executa o monitoramento em intervalos regulares
 */

const INTERVAL_MINUTES = 60; // Intervalo padrão: 1 hora
const INTERVAL_MS = INTERVAL_MINUTES * 60 * 1000;

let isRunning = false;
let executionCount = 0;

/**
 * Executa o monitoramento
 */
async function runMonitoring() {
  if (isRunning) {
    console.log('⚠️  Monitoramento anterior ainda em execução, pulando...');
    return;
  }

  isRunning = true;
  executionCount++;

  console.log(`\n${'='.repeat(80)}`);
  console.log(`Execução #${executionCount} - ${new Date().toLocaleString('pt-BR')}`);
  console.log('='.repeat(80));

  try {
    const result = await monitor();
    
    if (result.status === 'saved') {
      console.log('✓ Nova observação coletada e salva!');
    } else if (result.status === 'duplicate') {
      console.log('ℹ️  Nenhuma nova observação disponível');
    } else if (result.status === 'error') {
      console.error('✗ Erro durante a execução:', result.error);
    }
  } catch (error) {
    console.error('✗ Erro inesperado:', error.message);
  } finally {
    isRunning = false;
  }

  console.log(`Próxima execução em ${INTERVAL_MINUTES} minutos...`);
}

/**
 * Inicia o scheduler
 */
function startScheduler() {
  console.log('🚀 T CrB Monitoring Scheduler Iniciado');
  console.log(`⏰ Intervalo de execução: ${INTERVAL_MINUTES} minutos`);
  console.log(`📅 Iniciado em: ${new Date().toLocaleString('pt-BR')}`);
  console.log('\nPressione Ctrl+C para parar\n');

  // Executa imediatamente na primeira vez
  runMonitoring();

  // Agenda execuções periódicas
  const intervalId = setInterval(runMonitoring, INTERVAL_MS);

  // Tratamento de sinais para encerramento gracioso
  process.on('SIGINT', () => {
    console.log('\n\n🛑 Encerrando scheduler...');
    clearInterval(intervalId);
    console.log(`✓ Scheduler encerrado após ${executionCount} execuções`);
    process.exit(0);
  });

  process.on('SIGTERM', () => {
    console.log('\n\n🛑 Encerrando scheduler...');
    clearInterval(intervalId);
    console.log(`✓ Scheduler encerrado após ${executionCount} execuções`);
    process.exit(0);
  });
}

// Inicia o scheduler se for executado diretamente
if (import.meta.url === `file://${process.argv[1]}`) {
  startScheduler();
}

export { startScheduler, runMonitoring };