import Database from 'better-sqlite3';
import path from 'path';
import fs from 'fs';

const DB_DIR = path.join(process.cwd(), 'data');
const DB_PATH = path.join(DB_DIR, 'observations.db');

/**
 * Inicializa o banco de dados SQLite
 * @returns {Database} Instância do banco de dados
 */
function initDatabase() {
  // Cria o diretório data se não existir
  if (!fs.existsSync(DB_DIR)) {
    fs.mkdirSync(DB_DIR, { recursive: true });
  }

  const db = new Database(DB_PATH);
  
  // Cria a tabela se não existir
  db.exec(`
    CREATE TABLE IF NOT EXISTS observations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      star TEXT NOT NULL,
      jd TEXT NOT NULL UNIQUE,
      calendar_date TEXT NOT NULL,
      magnitude TEXT NOT NULL,
      error TEXT,
      filter TEXT NOT NULL,
      observer TEXT NOT NULL,
      scraped_at TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Cria índice para busca rápida por JD
  db.exec(`
    CREATE INDEX IF NOT EXISTS idx_jd ON observations(jd)
  `);

  // Cria índice para busca por data
  db.exec(`
    CREATE INDEX IF NOT EXISTS idx_calendar_date ON observations(calendar_date)
  `);

  console.log('Banco de dados inicializado:', DB_PATH);
  return db;
}

/**
 * Insere uma nova observação no banco de dados
 * @param {Database} db - Instância do banco de dados
 * @param {Object} data - Dados da observação
 * @returns {Object} Resultado da inserção
 */
function insertObservation(db, data) {
  try {
    const stmt = db.prepare(`
      INSERT INTO observations (star, jd, calendar_date, magnitude, error, filter, observer, scraped_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `);

    const result = stmt.run(
      data.star,
      data.jd,
      data.calendarDate,
      data.magnitude,
      data.error,
      data.filter,
      data.observer,
      data.timestamp
    );

    return { success: true, id: result.lastInsertRowid };
  } catch (error) {
    if (error.code === 'SQLITE_CONSTRAINT_UNIQUE') {
      return { success: false, error: 'duplicate', message: 'Observação já existe no banco de dados' };
    }
    throw error;
  }
}

/**
 * Verifica se uma observação já existe no banco de dados
 * @param {Database} db - Instância do banco de dados
 * @param {string} jd - Julian Date
 * @returns {boolean} True se existe
 */
function observationExists(db, jd) {
  const stmt = db.prepare('SELECT COUNT(*) as count FROM observations WHERE jd = ?');
  const result = stmt.get(jd);
  return result.count > 0;
}

/**
 * Obtém as últimas N observações
 * @param {Database} db - Instância do banco de dados
 * @param {number} limit - Número de observações a retornar
 * @returns {Array} Array de observações
 */
function getLatestObservations(db, limit = 10) {
  const stmt = db.prepare(`
    SELECT * FROM observations
    ORDER BY jd DESC
    LIMIT ?
  `);
  return stmt.all(limit);
}

/**
 * Obtém estatísticas do banco de dados
 * @param {Database} db - Instância do banco de dados
 * @returns {Object} Estatísticas
 */
function getStats(db) {
  const totalStmt = db.prepare('SELECT COUNT(*) as total FROM observations');
  const latestStmt = db.prepare('SELECT calendar_date, magnitude FROM observations ORDER BY jd DESC LIMIT 1');
  const oldestStmt = db.prepare('SELECT calendar_date FROM observations ORDER BY jd ASC LIMIT 1');

  const total = totalStmt.get();
  const latest = latestStmt.get();
  const oldest = oldestStmt.get();

  return {
    totalObservations: total.total,
    latestObservation: latest,
    oldestObservation: oldest
  };
}

/**
 * Exporta dados para CSV
 * @param {Database} db - Instância do banco de dados
 * @param {string} filename - Nome do arquivo CSV
 */
function exportToCSV(db, filename = 'export.csv') {
  const filepath = path.join(DB_DIR, filename);
  const observations = db.prepare('SELECT * FROM observations ORDER BY jd DESC').all();

  const header = 'ID,Star,JD,Calendar Date,Magnitude,Error,Filter,Observer,Scraped At,Created At\n';
  const rows = observations.map(obs => 
    `${obs.id},"${obs.star}","${obs.jd}","${obs.calendar_date}","${obs.magnitude}","${obs.error}","${obs.filter}","${obs.observer}","${obs.scraped_at}","${obs.created_at}"`
  ).join('\n');

  fs.writeFileSync(filepath, header + rows);
  console.log(`Dados exportados para: ${filepath}`);
  return filepath;
}

export {
  initDatabase,
  insertObservation,
  observationExists,
  getLatestObservations,
  getStats,
  exportToCSV
};