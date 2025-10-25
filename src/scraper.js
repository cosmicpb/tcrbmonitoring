import fetch from 'node-fetch';
import * as cheerio from 'cheerio';
import fs from 'fs';
import path from 'path';

const AAVSO_URL = 'https://apps.aavso.org/webobs/results/?star=t+crb&num_results=20&obs_types=all&page=1';

/**
 * Extrai os dados da observação mais recente da estrela T CrB
 * @returns {Promise<Object>} Objeto com os dados da observação
 */
async function scrapeLatestObservation() {
  try {
    console.log('Buscando dados da AAVSO...');
    const response = await fetch(AAVSO_URL);
    const html = await response.text();
    
    const $ = cheerio.load(html);
    
    // Encontra a primeira linha da tabela de observações (mais recente)
    const firstRow = $('table.observations tbody tr.obs').first();
    
    if (firstRow.length === 0) {
      throw new Error('Nenhuma observação encontrada na página');
    }
    
    // Extrai os dados das células
    // A tabela tem 3 colunas vazias no início (colspan="3")
    const cells = firstRow.find('td');
    
    const data = {
      star: $(cells[1]).text().trim(),           // Star (índice 1, após as 3 colunas vazias)
      jd: $(cells[2]).text().trim(),             // JD
      calendarDate: $(cells[3]).text().trim(),   // Calendar Date
      magnitude: $(cells[4]).find('a').text().trim() || $(cells[4]).text().trim(), // Magnitude
      error: $(cells[5]).text().trim(),          // Error
      filter: $(cells[6]).text().trim(),         // Filter
      observer: $(cells[7]).text().trim(),       // Observer
      timestamp: new Date().toISOString()
    };
    
    console.log('Dados extraídos:', data);
    return data;
    
  } catch (error) {
    console.error('Erro ao fazer scraping:', error.message);
    throw error;
  }
}

/**
 * Salva os dados em um arquivo CSV
 * @param {Object} data - Dados da observação
 * @param {string} filename - Nome do arquivo CSV
 */
function saveToCSV(data, filename = 'observations.csv') {
  const dataDir = path.join(process.cwd(), 'data');
  
  // Cria o diretório data se não existir
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }
  
  const filepath = path.join(dataDir, filename);
  const fileExists = fs.existsSync(filepath);
  
  // Cabeçalho do CSV
  const header = 'Star,JD,Calendar Date,Magnitude,Error,Filter,Observer,Timestamp\n';
  
  // Linha de dados
  const row = `"${data.star}","${data.jd}","${data.calendarDate}","${data.magnitude}","${data.error}","${data.filter}","${data.observer}","${data.timestamp}"\n`;
  
  if (!fileExists) {
    // Se o arquivo não existe, cria com cabeçalho
    fs.writeFileSync(filepath, header + row);
    console.log(`Arquivo criado: ${filepath}`);
  } else {
    // Se existe, apenas adiciona a nova linha
    fs.appendFileSync(filepath, row);
    console.log(`Dados adicionados ao arquivo: ${filepath}`);
  }
}

/**
 * Verifica se a observação já existe no CSV (evita duplicatas)
 * @param {Object} data - Dados da observação
 * @param {string} filename - Nome do arquivo CSV
 * @returns {boolean} True se já existe
 */
function observationExists(data, filename = 'observations.csv') {
  const filepath = path.join(process.cwd(), 'data', filename);
  
  if (!fs.existsSync(filepath)) {
    return false;
  }
  
  const content = fs.readFileSync(filepath, 'utf-8');
  // Verifica se já existe uma linha com o mesmo JD (Julian Date)
  return content.includes(`"${data.jd}"`);
}

/**
 * Função principal
 */
async function main() {
  try {
    const data = await scrapeLatestObservation();
    
    if (observationExists(data)) {
      console.log('Observação já existe no arquivo. Nenhuma ação necessária.');
    } else {
      saveToCSV(data);
      console.log('Nova observação salva com sucesso!');
    }
    
  } catch (error) {
    console.error('Erro na execução:', error);
    process.exit(1);
  }
}

// Executa se for chamado diretamente
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { scrapeLatestObservation, saveToCSV, observationExists };