import { scrapeLatestObservation, saveToCSV } from './scraper.js';
import { initDatabase, insertObservation, observationExists, getStats } from './database.js';

/**
 * Função principal que executa o monitoramento
 */
async function monitor() {
  console.log('=== T CrB Monitoring System ===');
  console.log(`Iniciado em: ${new Date().toLocaleString('pt-BR')}\n`);
  
  let db;
  
  try {
    // Inicializa o banco de dados
    db = initDatabase();
    
    // Extrai os dados mais recentes
    const data = await scrapeLatestObservation();
    
    // Verifica se já existe no banco de dados
    if (observationExists(db, data.jd)) {
      console.log('✓ Observação já registrada no banco de dados.');
      const stats = getStats(db);
      console.log(`\nEstatísticas: ${stats.totalObservations} observações no banco`);
      return { status: 'duplicate', data, stats };
    }
    
    // Salva no banco de dados
    const result = insertObservation(db, data);
    
    if (result.success) {
      console.log(`✓ Nova observação registrada no banco de dados (ID: ${result.id})`);
      
      // Também salva no CSV para backup
      saveToCSV(data);
      
      const stats = getStats(db);
      console.log(`\nEstatísticas: ${stats.totalObservations} observações no banco`);
      console.log(`Última magnitude: ${stats.latestObservation.magnitude}`);
      
      return { status: 'saved', data, id: result.id, stats };
    } else {
      console.log('✓ Observação já existe (duplicata detectada)');
      return { status: 'duplicate', data };
    }
    
  } catch (error) {
    console.error('✗ Erro durante o monitoramento:', error.message);
    return { status: 'error', error: error.message };
  } finally {
    if (db) {
      db.close();
    }
  }
}

// Executa se for chamado diretamente
if (import.meta.url === `file://${process.argv[1]}`) {
  monitor().then(result => {
    console.log('\nResultado:', result.status);
    if (result.status === 'error') {
      process.exit(1);
    }
  });
}

export { monitor };