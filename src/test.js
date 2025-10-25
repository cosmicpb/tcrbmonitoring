import { scrapeLatestObservation } from './scraper.js';

/**
 * Script de teste para verificar o funcionamento do scraper
 */
async function test() {
  console.log('=== Teste do Scraper T CrB ===\n');
  
  try {
    console.log('1. Testando extração de dados...');
    const data = await scrapeLatestObservation();
    
    console.log('\n2. Dados extraídos com sucesso:');
    console.log('   Star:', data.star);
    console.log('   JD:', data.jd);
    console.log('   Calendar Date:', data.calendarDate);
    console.log('   Magnitude:', data.magnitude);
    console.log('   Error:', data.error);
    console.log('   Filter:', data.filter);
    console.log('   Observer:', data.observer);
    console.log('   Timestamp:', data.timestamp);
    
    console.log('\n3. Validando dados...');
    const validations = [
      { field: 'star', valid: data.star.includes('CrB') || data.star.includes('CRB'), value: data.star },
      { field: 'jd', valid: data.jd.length > 0, value: data.jd },
      { field: 'calendarDate', valid: data.calendarDate.length > 0, value: data.calendarDate },
      { field: 'magnitude', valid: data.magnitude.length > 0, value: data.magnitude },
      { field: 'filter', valid: data.filter.length > 0, value: data.filter },
      { field: 'observer', valid: data.observer.length > 0, value: data.observer }
    ];
    
    let allValid = true;
    validations.forEach(v => {
      const status = v.valid ? '✓' : '✗';
      console.log(`   ${status} ${v.field}: ${v.value}`);
      if (!v.valid) allValid = false;
    });
    
    if (allValid) {
      console.log('\n✓ Todos os testes passaram!');
      console.log('\nPróximo passo: Execute "npm run scrape" para salvar os dados em CSV');
    } else {
      console.log('\n✗ Alguns testes falharam. Verifique os dados acima.');
      process.exit(1);
    }
    
  } catch (error) {
    console.error('\n✗ Erro durante o teste:', error.message);
    process.exit(1);
  }
}

test();