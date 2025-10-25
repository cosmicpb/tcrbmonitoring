import { initDatabase, getLatestObservations, getStats, exportToCSV } from './database.js';

/**
 * Script para visualizar dados do banco de dados
 */
function viewData() {
  console.log('=== Visualizador de Dados T CrB ===\n');
  
  const db = initDatabase();
  
  try {
    // Mostra estatísticas
    const stats = getStats(db);
    console.log('📊 Estatísticas:');
    console.log(`   Total de observações: ${stats.totalObservations}`);
    
    if (stats.latestObservation) {
      console.log(`   Última observação: ${stats.latestObservation.calendar_date}`);
      console.log(`   Magnitude atual: ${stats.latestObservation.magnitude}`);
    }
    
    if (stats.oldestObservation) {
      console.log(`   Primeira observação: ${stats.oldestObservation.calendar_date}`);
    }
    
    // Mostra as últimas 10 observações
    console.log('\n📋 Últimas 10 observações:');
    console.log('─'.repeat(100));
    console.log('ID  | JD           | Data              | Magnitude | Filtro | Observador');
    console.log('─'.repeat(100));
    
    const observations = getLatestObservations(db, 10);
    observations.forEach(obs => {
      console.log(
        `${String(obs.id).padEnd(4)}| ${obs.jd.padEnd(13)}| ${obs.calendar_date.padEnd(18)}| ${obs.magnitude.padEnd(10)}| ${obs.filter.padEnd(7)}| ${obs.observer}`
      );
    });
    console.log('─'.repeat(100));
    
    // Opção de exportar
    const args = process.argv.slice(2);
    if (args.includes('--export')) {
      console.log('\n📤 Exportando dados...');
      const filepath = exportToCSV(db);
      console.log(`✓ Dados exportados com sucesso!`);
    } else {
      console.log('\n💡 Dica: Use "node src/view-data.js --export" para exportar todos os dados para CSV');
    }
    
  } catch (error) {
    console.error('✗ Erro ao visualizar dados:', error.message);
    process.exit(1);
  } finally {
    db.close();
  }
}

viewData();